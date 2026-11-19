"""Resolve a public pack's logical names against a private candidate view."""
from dataclasses import dataclass, field, replace
import os
from pathlib import Path
import unicodedata


# A sibling consumer can identify ephemeral artifacts without guessing directory names.
ATTEMPT_MARKER = '.ec2-candidate-attempt'


def _nfc(value):
    return unicodedata.normalize('NFC', str(value))


def _relative(path, root):
    parts = Path(path).parts
    for base in (root, root.resolve()):
        prefix = base.parts
        if tuple(map(_nfc, parts[:len(prefix)])) == tuple(map(_nfc, prefix)):
            return Path(*parts[len(prefix):])
    raise ValueError(f'경로가 기준 폴더 밖에 있습니다: {path}')


def checked_file(root, relative):
    if root.is_symlink():
        raise ValueError(f'심볼릭 링크 경로 금지: {root}')
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError(f'상대 경로 필요: {relative}')
    current = root
    for part in path.parts:
        matches = [p for p in current.iterdir() if _nfc(p.name) == _nfc(part)] if current.is_dir() else []
        if len(matches) > 1:
            raise ValueError(f'NFC 경로 충돌: {current / part}')
        current = current / part if (current / part).exists() or not matches else matches[0]
        if current.is_symlink():
            raise ValueError(f'심볼릭 링크 경로 금지: {current}')
    current.resolve().relative_to(root.resolve())
    return current


@dataclass(frozen=True)
class PackPaths:
    repo: Path
    public_pack: Path
    candidate_pack: Path | None = None
    private_roots: tuple[Path, ...] = field(default=(), kw_only=True)
    _root_identity: Path = field(init=False, repr=False)

    def __post_init__(self):
        repo = Path(self.repo).absolute()
        public = Path(self.public_pack)
        public = public if public.is_absolute() else repo / public
        public = checked_file(repo, _relative(public, repo))
        if public == repo:
            raise ValueError('팩 하위 경로 필요')
        object.__setattr__(self, 'repo', repo)
        object.__setattr__(self, 'public_pack', public)
        if self.candidate_pack is not None:
            candidate = Path(self.candidate_pack).absolute()
            if '..' in candidate.parts or candidate.is_symlink():
                raise ValueError(f'후보 폴더 경로 오류: {candidate}')
            if candidate.resolve().is_relative_to(public.resolve()) or public.resolve().is_relative_to(candidate.resolve()):
                raise ValueError('공개 폴더와 후보 폴더가 겹칩니다')
            object.__setattr__(self, 'candidate_pack', candidate)
        object.__setattr__(self, '_root_identity', self.work_pack.resolve())

    def excluding(self, *roots: Path):
        """Carry known private producer and child RUN roots when rebinding a view."""
        private_roots = tuple(dict.fromkeys(root.resolve() for root in (*self.private_roots, *roots)))
        return replace(self, private_roots=private_roots)

    @property
    def work_pack(self) -> Path:
        return self.candidate_pack or self.public_pack

    def work_file(self, relative: str) -> Path:
        if self.work_pack.resolve() != self._root_identity:
            raise ValueError(f'후보 폴더 경로 변경: {self.work_pack}')
        return checked_file(self.work_pack, relative)

    def logical(self, path: Path) -> Path:
        """Public absolute name of a trusted view or repository path."""
        path = Path(path)
        if '..' in path.parts:
            raise ValueError(f'상위 경로 금지: {path}')
        if self.candidate_pack is not None:
            try:
                rel = _relative(path, self.candidate_pack)
            except ValueError:
                pass
            else:
                self.work_file(str(rel))
                return self.public_pack / rel
        return self.repo / _relative(path, self.repo) if path.is_absolute() else self.repo / path

    def source_file(self, logical_repo_path: str) -> Path:
        path = Path(logical_repo_path)
        if '..' in path.parts:
            raise ValueError(f'상위 경로 금지: {path}')
        path = path if path.is_absolute() else self.repo / path
        relative = _relative(path, self.repo)
        if _nfc(self.logical(path)) != _nfc(self.repo / relative):
            raise ValueError(f'후보 경로 대신 공개 경로 필요: {path}')
        try:
            local = _relative(path, self.public_pack)
        except ValueError:
            source = checked_file(self.repo, relative)
            if self.candidate_pack:
                resolved = source.resolve()
                if any(resolved.is_relative_to(root) for root in self.private_roots):
                    raise ValueError(f'임시 시도 경로 대신 공개 경로 필요: {path}')
                for parent in source.parents:
                    if parent == self.repo:
                        break
                    if (parent / ATTEMPT_MARKER).is_file():
                        raise ValueError(f'임시 시도 경로 대신 공개 경로 필요: {path}')
            return source
        return self.work_file(str(local))

    def link(self, logical_dir: Path, href_path: str) -> Path:
        """Local URLs may climb to course sources; normalize only within the repository."""
        if Path(href_path).is_absolute():
            raise ValueError(f'절대 링크 금지: {href_path}')
        return self.source_file(os.path.normpath(self.logical(logical_dir) / href_path))
