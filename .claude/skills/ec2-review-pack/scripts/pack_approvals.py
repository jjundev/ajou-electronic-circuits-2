"""Target identities and physical evidence for opt-in parallel review attempts."""
import hashlib
import json
import platform
import re
import os
import tempfile
import sys
from pathlib import Path

import pack_flow as f


POLICY = 'ec2-target-review-v1'
VIEWS = ('desktop-light', 'desktop-dark', 'mobile-light', 'mobile-dark')
ROLES = {'explain-blind', 'pdf-qa', 'browser-qa', 'standalone-svg-qa'}


def digest(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(encoded.encode()).hexdigest()


def approval_key(kind: str, target: str, *, input_hashes: dict[str, str], policy_version: str) -> str:
    return digest([kind, target, input_hashes, policy_version])


def _valid(row, root, hashes):
    if row.get('status') != 'pass' or not row.get('reviewer') or not row.get('evidence') or not row.get('files'):
        return False
    if row.get('target', '').startswith(('note-visual:', 'pdf-page:', 'standalone-svg:')):
        if not any(Path(r['path']).suffix.lower() == '.png' for r in row['files']):
            return False
    for record in row['files']:
        path = Path(record['path'])
        if not path.is_absolute() or not f.within(path.resolve(), root.resolve()) or not path.is_file():
            return False
        if path not in hashes:
            hashes[path] = f._sha(path)
        if hashes[path] != record['sha256']:
            return False
    return True


def select_approval(ledger: list[dict], *, key: str, run_root: Path) -> dict | None:
    row = next((r for r in reversed(ledger) if r['key'] == key), None)
    return row if row and _valid(row, run_root, {}) else None


def collect_current_reviews(required: dict[str, str], ledger: list[dict], *, run_root: Path) -> dict:
    current, pending, hashes = {}, {}, {}
    for target, key in required.items():
        candidates = [r for r in reversed(ledger) if r['target'] == target]
        matched = [r for r in candidates if r['key'] == key]
        row = matched[0] if matched and _valid(matched[0], run_root, hashes) else None
        if row:
            current[target] = row
        else:
            if matched and matched[0].get('status') == 'invalidated':
                pending[target] = matched[0]['reason']
                continue
            pending[target] = ('original evidence missing or changed' if matched else
                               'target inputs or policy changed' if candidates else 'first inspection')
    return dict(current=current, pending=pending)


def blind_targets(questions, sealed, profile):
    from learning_style import PERSONALIZED_REVIEW_POLICY
    rows = {}
    for question in questions:
        workbook = question['workbook_id']
        inputs = {k: digest(question[k]) for k in ('title', 'original_html', 'conditions_html', 'ask_html', 'subparts')}
        inputs['figures'] = digest([f._sha(sealed/name) for name in question['figures']])
        inputs['profile'] = profile
        inputs['solution_policy'] = PERSONALIZED_REVIEW_POLICY
        for sub in question['subparts']:
            target = f'independent:{workbook}:{sub}'
            rows[target] = dict(key=approval_key('independent', target, input_hashes=inputs, policy_version=POLICY),
                                item=question['id'] + ':' + sub)
    return rows


def render_fingerprint(browser_version, resources):
    import pymupdf
    inputs = [(r['path'], r['sha256']) if isinstance(r, dict) else (str(r), f._sha(Path(r))) for r in resources]
    return digest([browser_version, platform.platform(), pymupdf.VersionBind, inputs, 'rgb-96dpi-v1'])


def _geometry(page):
    """Print-space glyph boxes near narrow stroked geometry; humans adjudicate."""
    import pymupdf as fitz
    segments = []
    for path in page.get_drawings():
        if path['type'] not in ('s', 'fs'):
            continue
        for item in path['items']:
            if item[0] == 'l':
                box = fitz.Rect(item[1], item[2]).normalize()
                segments.append(box + (-0.5, -0.5, 0.5, 0.5))
    hints = []
    for block in page.get_text('rawdict', flags=0)['blocks']:
        for line in block.get('lines', []):
            for span in line['spans']:
                chars = span['chars']
                label = ''.join(c['c'] for c in chars).strip()
                if not label or len(label) > 24 or not re.search(r'[a-zA-ZπΩβ+-]', label):
                    continue
                for char in chars:
                    box = fitz.Rect(char['bbox'])
                    margin = span['size'] * .6
                    nearby = box + (-margin, -margin, margin, margin)
                    segment = next((seg for seg in segments if nearby.intersects(seg)), None)
                    if segment is not None:
                        hints.append(dict(label=label, glyph=list(box), geometry=list(segment), units='pt'))
                        break
    return hints


def pdf_targets(pdf, overlay, directory, fingerprint, *, order=None):
    """Render *all* current pages before computing any reusable page identity."""
    import pymupdf
    directory.mkdir(parents=True, exist_ok=True)
    problems = overlay['problems']
    ids = [p['id'] for p in problems]
    pages = []
    with pymupdf.open(pdf) as document:
        if not document.is_pdf or not len(document):
            raise f.FlowError('empty PDF page inventory')
        pdf_digest = f._sha(pdf)
        ordered = (isinstance(order, dict) and order.get('schema_version') == 1 and
                   order.get('pdf_sha256') == pdf_digest and order.get('count') == len(document) and
                   isinstance(order.get('pages'), list) and len(order['pages']) == len(document) and
                   all(isinstance(p, dict) and {'id', 'owner'} <= p.keys() for p in order['pages']))
        mapping = order['pages'] if ordered else [{} for _ in document]
        order_identity = digest([ids, mapping, order.get('browser_version') if ordered else pdf_digest])
        for n, page in enumerate(document, 1):
            image = directory/f'page-{n:0{len(str(len(document)))}d}.png'
            pix = page.get_pixmap(dpi=96, alpha=False)
            pix.save(image)
            owner = mapping[n-1].get('owner')
            pages.append((image, ids.index(owner) if owner in ids else None, _geometry(page)))
    rows = {}
    for n, (image, owner, hints) in enumerate(pages, 1):
        target = 'pdf-page:' + str(n)
        inputs = dict(render_fingerprint=fingerprint, page_image=f._sha(image), order=order_identity,
                      count=str(len(pages)), explanation=digest(problems[owner] if owner is not None else problems),
                      assets=digest(overlay.get('assets', {})), profile=digest(overlay['learning_style']),
                      overlay_policy=digest(overlay.get('review_policy_version')))
        rows[target] = dict(key=approval_key('pdf-page', target, input_hashes=inputs, policy_version=POLICY),
                            owner=ids[owner] if owner is not None else None, image=str(image),
                            image_sha256=inputs['page_image'], geometry_candidates=hints)
    return rows


def resource_paths(state, brief):
    repo = Path(state['repo'])
    vendor = repo/'.claude/skills/ec2-problem-explain/assets/vendor'
    resources = [p for p in vendor.rglob('*') if p.is_file()]
    resources.extend(p for p in (repo/'workbook/templates').glob('*') if p.is_file())
    resources.extend(Path(p) for p in brief['references'] if Path(p).is_file())
    return sorted(set(resources))


def environment_id(state):
    from importlib.metadata import distribution, version
    version_path = state['actions'].get('render-preflight', {}).get('artifacts', {}).get('render-preflight.json')
    browser = f._read(version_path).get('browser_version') if version_path else None
    # Playwright's own release pins a Chromium revision when note QA precedes
    # workbook preflight. Its offline route and host OS are part of the contract.
    import pymupdf
    bundle = distribution('playwright').locate_file('playwright/driver/package/browsers.json')
    chromium = next(row for row in json.loads(Path(bundle).read_text())['browsers'] if row['name'] == 'chromium')
    return dict(preflight_browser=browser, bundled_browser=chromium['browserVersion'], playwright=version('playwright'),
                platform=platform.platform(), pymupdf=pymupdf.VersionBind)


def served_files(brief):
    if brief['role'] != 'browser-qa':
        return []
    from pack_parallel import local_path
    root = Path(brief['candidate_pack'])
    return sorted(local_path(root, p.relative_to(root).as_posix()) for p in root.rglob('*') if p.is_file())


def environment_current(state, brief, manifest):
    return (manifest['environment'] == environment_id(state) and
            [r['path'] for r in manifest['served']] == [str(f.nfc_path(p)) for p in served_files(brief)] and
            [r['path'] for r in manifest['files']] == [str(f.nfc_path(p)) for p in resource_paths(state, brief)])


def static_views(note, root, topics):
    """Measure actual viewport output for inert, local documents only."""
    from browser_runtime import local_url, install_render_routes, launch_chromium
    from playwright.sync_api import Error, sync_playwright
    raw = note.read_text()
    if re.search(r'<(?:script|iframe|object|embed|video|canvas|meta[^>]*refresh)\b|\son\w+\s*=|@(?:import|keyframes)', raw, re.I):
        return None
    results = {}
    with sync_playwright() as pw:
        browser = launch_chromium(pw)
        try:
            for view in VIEWS:
                mobile, dark = view.startswith('mobile'), view.endswith('dark')
                page = browser.new_page(viewport={'width':375 if mobile else 1280, 'height':812 if mobile else 900},
                                        color_scheme='dark' if dark else 'light', offline=True, service_workers='block',
                                        java_script_enabled=False)
                try:
                    blocked = set()
                    install_render_routes(page, local_roots=(root,), blocked=blocked)
                    page.on('response', lambda r: blocked.add(r.url) if r.status >= 400 else None)
                    page.goto(local_url(note,root))
                    page.evaluate('document.fonts.ready')
                    shell = page.evaluate("""ids => {
                        const clone = document.documentElement.cloneNode(true);
                        for (const id of ids) clone.querySelector('#'+CSS.escape(id))?.replaceChildren();
                        return clone.outerHTML;
                    }""", topics)
                    for topic in topics:
                        # Only isolate explicit, non-nested articles. The viewport
                        # includes any sidebar or neighbouring material actually visible.
                        loc = page.locator('article[id=' + json.dumps(topic) + ']')
                        if loc.count() != 1:
                            return None
                        markup = loc.evaluate('e=>e.outerHTML')
                        loc.evaluate("e=>e.scrollIntoView({block:'start'})")
                        pixels = hashlib.sha256(page.screenshot(animations='disabled')).hexdigest()
                        results[(topic, view)] = digest([shell, markup, pixels, browser.version])
                    if blocked:
                        return None
                finally:
                    page.close()
        except Error:
            return None
        finally:
            browser.close()
    return results


def uncertain_svg(markup):
    """Accept self-contained image/font data and same-document fragments."""
    import xml.etree.ElementTree as ET
    try:
        svg = ET.fromstring(markup)
    except ET.ParseError:
        return True
    if re.search(r'@import|@keyframes|<\?xml-stylesheet|<!DOCTYPE|\\', markup, re.I):
        return True
    refs = []
    for node in svg.iter():
        if node.tag.split('}')[-1].lower() in ('script', 'foreignobject', 'animate', 'set', 'animatetransform', 'animatemotion'):
            return True
        for key, value in node.attrib.items():
            name = key.split('}')[-1].lower()
            if name.startswith('on'):
                return True
            if name in ('href', 'src'):
                refs.append(value)
    refs.extend(re.findall(r'url\(\s*([^)]*)\)', markup, re.I))
    return any(not ref.strip().strip('\"\'').lower().startswith(
        ('#', 'data:font/', 'data:image/png;', 'data:image/jpeg;', 'data:image/webp;')) for ref in refs)


def _visual_targets(state, brief, fingerprint, *, served=None):
    # The page's scripts, layout and shared assets can affect every topic.
    # Bind the whole served candidate inventory. A standalone SVG with external
    # dependencies additionally binds its complete converted directory.
    role = brief['role']
    root = Path(brief.get('candidate_pack', Path(brief['note']).parent))
    converted = brief.get('converted_assets', {})
    rows = {}
    if role == 'browser-qa':
        from pack_parallel import file_records
        if served is None:
            served = file_records(served_files(brief))
        note = root/Path(brief['note']).name
        if not note.is_file() or f._sha(note) != f._sha(Path(brief['note'])):
            raise f.FlowError('served browser candidate differs from assembled note')
        resources = digest([(Path(r['path']).relative_to(root).as_posix(), r['sha256'])
                            for r in served if Path(r['path']) != note])
        views = static_views(note, root, brief['targets'])
        # Unbounded scripts or unresolved resources have no provably stable
        # target rendering. A fresh attempt must inspect the entire group.
        group = digest([f._sha(note), resources, brief['attempt']]) if views is None else None
        for topic in brief['targets']:
            for view in VIEWS:
                target = f'note-visual:{topic}:{view}'
                inputs = dict(target_group=group or views[(topic,view)], resources=resources, render_fingerprint=fingerprint)
                rows[target] = dict(owner=topic, key=approval_key('note-visual', target, input_hashes=inputs, policy_version=POLICY))
    else:
        for record in converted['svgs']:
            path = Path(record['path'])
            name = path.relative_to(Path(converted['md']['path']).parent).as_posix()
            target = 'standalone-svg:' + name
            inputs = dict(svg=f._sha(path), render_fingerprint=fingerprint)
            raw = path.read_text()
            # Converted SVGs normally embed their font/data. Unknown external
            # resources cannot authorize another attempt's standalone rendering.
            if uncertain_svg(raw):
                inputs['uncertain_dependencies'] = brief['attempt']
            rows[target] = dict(key=approval_key('standalone-svg', target, input_hashes=inputs, policy_version=POLICY),
                                owner=record['path'], image=brief['svg_screenshots'][record['path']])
    return rows


def make_plan(state, brief):
    role = brief['role']
    if role not in ROLES:
        return
    run = Path(state['run'])
    snapshot = f._read(run/'learning-style.json')
    profile = digest(snapshot)
    if role == 'explain-blind':
        path = Path(brief['questions'])
        rows = blind_targets(f._read(path)['problems'], path.parent, profile)
    else:
        from pack_parallel import file_records
        resources = resource_paths(state, brief)
        environment = environment_id(state)
        records = file_records(resources)
        fingerprint = render_fingerprint([profile, environment, POLICY], records)
        manifest_path = Path(brief['run'])/'render-environment.json'
        served = file_records(served_files(brief))
        f._atomic_json(manifest_path, dict(environment=environment, files=records, served=served))
        brief['render_environment'] = dict(path=str(manifest_path), sha256=f._sha(manifest_path))
        brief['render_fingerprint'] = fingerprint
        brief['render_context'] = dict(engine='Chromium', version=environment['preflight_browser'] or environment['bundled_browser'],
                                       platform=environment['platform'])
        if role == 'pdf-qa':
            order = state['actions']['build-answers']['artifacts'].get('page-order.json')
            mapping = f._read(order) if order else None
            rows = pdf_targets(Path(brief['pdf']), f._read(brief['overlay']), Path(brief['run'])/'rendered-pages',
                               fingerprint, order=mapping)
            hints = Path(brief['run'])/'print-geometry.json'
            f._atomic_json(hints, {t:r.pop('geometry_candidates') for t,r in rows.items()})
            brief['geometry_hints'] = dict(path=str(hints), sha256=f._sha(hints))
        else:
            rows = _visual_targets(state, brief, fingerprint, served=served)
    required = {target: row['key'] for target, row in rows.items()}
    ledger = state.get('approval_ledger', [])
    result = collect_current_reviews(required, ledger, run_root=run)
    if role == 'explain-blind':
        author = state['tasks']['explain-author'].get('agent_id')
        for target, row in list(result['current'].items()):
            if row['reviewer'] == author:
                del result['current'][target]
                result['pending'][target] = 'previous solver is the current author'
    for finding in brief.get('recheck_findings', []):
        affected = affected_targets(rows, finding['target'])
        for t in affected:
            result['current'].pop(t, None)
            result['pending'][t] = 'requested repair inspection'
    brief['approval_plan'] = dict(targets=rows, pending=result['pending'],
                                  reusable={t:r['key'] for t,r in result['current'].items()})


def target_contract(state, task, receipt, *, write=False):
    try:
        return _target_contract(state, task, receipt, write=write)
    except f.FlowError:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise f.FlowError('invalid target review: ' + str(exc)) from exc


def _target_contract(state, task, receipt, *, write):
    """Compose existing role artifacts from named decisions and original evidence."""
    from pack_parallel import local_path
    from pack_receipts import obj, require, _png, cached_sha
    root = Path(task['attempt_dir'])
    run = Path(state['run'])
    brief = obj(task['brief'])
    plan = brief['approval_plan']
    role = task['role']
    source = root/'target-reviews.json'
    require(str(source) in receipt['reviews'], 'target-reviews.json required')
    require(local_path(root, source.name) == source, 'target reviews outside attempt')
    decisions = obj(source)
    require(set(decisions) == set(plan['pending']), 'submit one actual judgment for every pending target')
    reviewer = task.get('agent_id')
    require(isinstance(reviewer, str) and reviewer.strip(), 'bound reviewer required')
    frozen, pending = plan['reusable'], plan['pending']
    old = collect_current_reviews(frozen, state.get('approval_ledger', []), run_root=run)
    require(not old['pending'], 'previous approval evidence changed after claim')
    fresh, reused, outputs, inputs, items = {}, {}, [], {}, {}
    used_images = set()
    hashes = {}
    def file_hash(path):
        return cached_sha(path, hashes)
    pdf_evidence = []
    hints = obj(brief['geometry_hints']['path']) if role == 'pdf-qa' else {}
    def materialize(path, data):
        path = local_path(root, path.relative_to(root).as_posix())
        if write and (not path.exists() or path.read_bytes() != data):
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as out:
                out.write(data)
            os.replace(out.name, path)
        require(path.is_file() and path.read_bytes() == data, 'target evidence mismatch: ' + path.name)
        outputs.append(str(path))
    def json_output(name, value):
        materialize(root/name, (json.dumps(value, ensure_ascii=False, sort_keys=True) + '\n').encode())
    if role == 'explain-blind':
        child_scripts = Path(__file__).resolve().parents[2]/'ec2-problem-explain/scripts'
        sys.path.insert(0, str(child_scripts))
        try:
            from epe_independent import independent_errors
        finally:
            sys.path.remove(str(child_scripts))
    for index, (target, spec) in enumerate(plan['targets'].items(), 1):
        if role == 'pdf-qa':
            canonical = local_path(root, Path(spec['image']).relative_to(root).as_posix())
            require(canonical.is_file() and file_hash(canonical) == spec['image_sha256'], 'current rendered page missing or changed')
            outputs.append(str(canonical))
        if target in pending:
            decision = decisions[target]
            require(isinstance(decision, dict) and decision.get('status') == 'pass'
                    and isinstance(decision.get('evidence'), str) and decision['evidence'].strip(),
                    'explicit passing target judgment and evidence required')
            files = [source, Path(receipt['report'])]
            row = dict(target=target, key=spec['key'], status='pass', reviewer=reviewer,
                       evidence=decision['evidence'], attempt=task['attempt'], decision=decision)
            if role in ('browser-qa', 'standalone-svg-qa'):
                require(decision.get('renderer') == brief['render_context'],
                        'record the actual inspection renderer and platform for reusable screen proof')
            if role != 'explain-blind':
                image = Path(decision['image'])
                require(image.is_absolute() and f.within(image, root), 'fresh screen outside claimed attempt')
                local_path(root, image.relative_to(root).as_posix())
                if role == 'browser-qa':
                    require(not image.is_relative_to(root/'review-screens'), 'fresh screen uses runner output directory')
                if role == 'standalone-svg-qa':
                    require(image == Path(spec['image']), 'standalone screen must match its claimed SVG')
                _png(image)
                require(image not in used_images, 'distinct target inspections require distinct screens')
                used_images.add(image)
                if role == 'pdf-qa':
                    if hints[target]:
                        text = decision.get('geometry_evidence')
                        require(isinstance(text, str) and text.strip(), 'human PDF geometry adjudication required')
                    require(image == Path(spec['image']) and file_hash(image) == spec['image_sha256']
                            and decision.get('overflow') == [], 'inspect actual candidate page and adjudicate overflow')
                row['screen'] = str(image)
                files.append(image)
                outputs.append(str(image))
            row['files'] = [dict(path=str(p), sha256=file_hash(p)) for p in dict.fromkeys(files)]
            fresh[target] = row
        else:
            row = old['current'][target]
            reused[target] = row['key']
            for record in row['files']:
                inputs[record['path']] = record['sha256']
        if role == 'explain-blind':
            decision = row['decision']
            errors = independent_errors(spec['item'], decision)
            require(not errors, '; '.join(errors))
            items[spec['item']] = {k:v for k,v in decision.items()
                                   if k in ('status','method','conclusion','evidence','tolerance','residual')}
            items[spec['item']]['reviewer'] = row['reviewer']
        else:
            image = Path(row['screen'])
            if role == 'pdf-qa':
                require(file_hash(image) == spec['image_sha256'], 'original PDF screen differs from current page')
                dest = root/'answer-pages'/Path(spec['image']).name
                pdf_evidence.append(dest)
            elif role == 'standalone-svg-qa':
                dest = Path(spec['image'])
            else:
                dest = root/'review-screens'/f'{index:04}.png'
            materialize(dest, image.read_bytes())
    if role == 'explain-blind':
        # The blind worker can run build/check repeatedly. Its directory must
        # never reveal another solver's answers, even after its own submission.
        own = {plan['targets'][t]['item'] for t in fresh}
        json_output('independent.json', dict(items={k:v for k,v in items.items() if k in own}))
    if role == 'pdf-qa':
        overlay = obj(brief['overlay'])
        files = [Path(receipt['report']), *pdf_evidence]
        review = dict(schema_version=1, status='pass', reviewer=reviewer, overflow=[],
                      pdf_sha256=file_hash(Path(brief['pdf'])), overlay_sha256=file_hash(Path(brief['overlay'])),
                      learning_style_sha256=overlay['learning_style']['sha256'],
                      evidence=[dict(path=p.relative_to(root).as_posix(), sha256=file_hash(p)) for p in files],
                      page_reviewers={t:r['reviewer'] for t,r in {**old['current'], **fresh}.items()})
        json_output('answer-review.json', review)
        outputs.append(str(root/'answer-review.md'))
    return dict(fresh=fresh, reused=reused, outputs=sorted(set(outputs)), evidence=inputs, independent=items)


def affected_targets(rows, owner):
    affected = {t for t,r in rows.items() if t == owner or r.get('owner') == owner}
    # Unknown ownership (including a PDF hint page) cannot exclude a defect.
    return (affected | {t for t,r in rows.items() if not r.get('owner')}) if affected else set(rows)


def adopt_targets(state, task, receipt):
    brief = f._read(task['brief'])
    plan = brief.get('approval_plan')
    if not plan:
        return
    state.setdefault('approval_history', []).append(dict(task=task['id'], attempt=task['attempt'],
        brief=task['artifacts'].get('brief.json', task['brief']), status=receipt['status'],
        pending=plan['pending'], reused=receipt.get('reused_approvals', {})))
    if receipt['task_status'] == 'needs_fix':
        for finding in receipt['unresolved']:
            for target in affected_targets(plan['targets'], finding['target']):
                state.setdefault('approval_ledger', []).append(dict(target=target, key=plan['targets'][target]['key'],
                    status='invalidated', reviewer=task['agent_id'], attempt=task['attempt'],
                    reason='later finding: ' + finding['rule'], finding=finding))
    root = Path(task['attempt_dir'])
    for row in receipt.get('fresh_approvals', {}).values():
        # Retain original human files AND their immutable, adopted counterparts.
        frozen = dict(row)
        files = {r['path']:r['sha256'] for r in row['files']}
        for path, sha in list(files.items()):
            copied = task['artifacts'][Path(path).relative_to(root).as_posix()]
            files[copied] = sha
            if path == frozen.get('screen'):
                frozen['screen'] = copied
        frozen['files'] = [dict(path=p, sha256=h) for p,h in files.items()]
        state.setdefault('approval_ledger', []).append(frozen)
