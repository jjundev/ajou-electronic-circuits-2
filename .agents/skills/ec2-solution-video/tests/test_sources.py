from fixtures import *
from solution_video.sources import discover,freeze_sources,validate_pairs
from solution_video.contracts import InputError
class SourceTests(Sandbox):
    def test_wide_exam_badge_can_share_text_line_with_title(self):
        pairs=discover(REPO,'0918',None)
        self.assertEqual(len(pairs),10)
        self.assertEqual({p['problem_id'] for p in pairs if p['problem_id'].startswith('202')},
                         {'2021-1_중간-Q5','2023-1_중간-Q2'})
    def test_wide_conditions_compare_entire_panel(self):
        import fitz
        refs=[]
        for i in range(2):
            p=self.run/f'wide{i}.pdf';d=fitz.open();pg=d.new_page(width=1440,height=810)
            pg.draw_rect((36,61,487,657),fill=(246/255,246/255,243/255),color=None)
            pg.insert_text((400,160),'I = '+str(i+1));d.save(p)
            refs.append(dict(snapshot=str(p),page_index=0,width_pt=1440,height_pt=810))
        with self.assertRaisesRegex(InputError,'conditions differ'):
            validate_pairs([dict(problem_id='E10.11',problem=refs[0],answer=refs[1])])
    def test_1002_pairs_skip_hint(self):
        pairs=discover(REPO,'1002',None); self.assertEqual(len(pairs),10); self.assertTrue(all(p['md_snapshot'] for p in pairs))
        self.assertEqual(next(p for p in pairs if p['problem_id']=='E10.11')['answer']['page_index'],1)
        self.assertEqual(next(p for p in pairs if p['problem_id']=='2021-1_중간-Q3')['problem']['page_index'],7)
        frozen=freeze_sources(pairs,self.run); self.assertFalse(Path(frozen[0]['answer']['snapshot']).is_absolute())
        self.assertTrue((self.run/frozen[0]['answer']['snapshot']).is_file())
    def test_ambiguous_pair_and_duplicate_conflict(self):
        for selector in ['0931','1002-0911','bad']:
            with self.assertRaises(InputError): discover(REPO,selector,None)
        with self.assertRaises(InputError): discover(REPO,'1002',['E10.99'])
        pairs=discover(REPO,'1002',['E10.11']); self.assertEqual(len(pairs),1)
        duplicate=dict(pairs[0],answer=dict(pairs[0]['answer'],page_index=2))
        with self.assertRaises(InputError): validate_pairs(pairs+[duplicate])
    def test_zero_padded_actual_dates_and_selected_only(self):
        self.assertTrue(discover(REPO,'0923',None));self.assertTrue(discover(REPO,'0930',None))
        self.assertEqual(len(discover(REPO,'0930',['E10.16'])),1)
        root=self.run/'selected';folder=root/'복습노트/1002';folder.mkdir(parents=True)
        import shutil
        for p in (REPO/'복습노트/1002').glob('*.pdf'):shutil.copyfile(p,folder/p.name)
        (folder/'problems.txt').write_text('E10.11 | valid\nE10.99 | unrelated missing page\n')
        self.assertEqual(len(discover(root,'1002',['E10.11'])),1)
    def test_pagination_is_not_a_different_solution(self):
        import fitz
        pairs=[]
        for i in range(2):
            p=self.run/f'page{i}.pdf';d=fitz.open();pg=d.new_page(width=842,height=595)
            pg.insert_text((25,35),'E10.11');pg.insert_text((320,200),'x = 1');pg.insert_text((700,585),f'{i+1} / 2');d.save(p)
            ref=dict(snapshot=str(p),page_index=0,width_pt=842,height_pt=595);pairs.append(dict(problem_id='E10.11',problem=ref,answer=ref,md_snapshot=None))
        validate_pairs(pairs)
    def test_duplicate_footer_preserves_all_frozen_correspondences(self):
        import fitz
        root=self.run/'dedup'
        for i,date in enumerate(['1001','1002']):
            folder=root/'복습노트'/date;folder.mkdir(parents=True);(folder/'problems.txt').write_text('E10.11 | identical\n')
            for role in ['문제','답안']:
                d=fitz.open();p=d.new_page(width=842,height=595);p.insert_text((25,35),'E10.11');p.insert_text((320,200),'x = 1');p.insert_text((700,585),f'{i+1} / 2');d.save(folder/f'{date}-{role}.pdf')
        pairs=discover(root,'1001-1002');self.assertEqual(len(pairs),1);self.assertEqual(pairs[0]['dates'],['1001','1002']);self.assertEqual(len(pairs[0]['sources']),2)
        batch=self.run/'frozen';frozen=freeze_sources(pairs,batch)
        self.assertTrue(all((batch/s['answer']['snapshot']).is_file() for s in frozen[0]['sources']))
    def test_malformed_pdf_isolated_in_batch_discovery(self):
        import shutil
        root=self.run/'partial';bad=root/'복습노트/1001';good=root/'복습노트/1002';bad.mkdir(parents=True);good.mkdir()
        (bad/'problems.txt').write_text('P10.01 | malformed\n');(good/'problems.txt').write_text('E10.11 | valid\n')
        for role in ['문제','답안']:(bad/f'bad-{role}.pdf').write_bytes(b'not a pdf')
        for p in (REPO/'복습노트/1002').glob('*.pdf'):shutil.copyfile(p,good/p.name)
        errors=[];pairs=discover(root,'1001-1002',failures=errors)
        self.assertEqual([p['problem_id'] for p in pairs],['E10.11']);self.assertEqual(errors[0]['problem_id'],'P10.01')
