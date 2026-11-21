"""Real Git regression tests for Lab06/07 committed-input checks."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from learning_project import lab06_reporting, lab07_reporting
from learning_project.workflow import WorkflowError


class CommittedInputEolTests(unittest.TestCase):
    def test_git_normalized_text_but_not_content_or_binary_changes(self):
        for lab in (6, 7):
            with self.subTest(lab=lab), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                def git(*args):
                    return subprocess.check_output(['git', '-C', str(root), *args])
                git('init', '-q', '-b', 'student/eol-test')
                git('config', 'core.autocrlf', 'true')
                git('config', 'core.safecrlf', 'false')
                report = root / f'reports/lab{lab:02}'
                report.mkdir(parents=True)
                (report / 'REPORT.md').write_bytes('Особиста гілка: student/eol-test\n'.encode())
                text = report / 'decision-input.json'
                text.write_bytes(b'{"value": 1}\n')
                binary = report / 'capture.png'
                binary.write_bytes(b'\x00PNG\r\nbytes\n')
                # Explicit binary attribute must remain byte-exact even without NUL.
                (root / '.gitattributes').write_bytes(b'*.png -text\n')
                corpus = root / 'corpus.json'
                corpus.write_bytes(b'{}\n')
                collection = root / 'student/collection'
                collection.mkdir(parents=True)
                git('add', '.')
                git('-c', 'user.name=Synthetic Test', '-c', 'user.email=test@example.invalid',
                    'commit', '-qm', 'Synthetic EOL regression fixture')
                head = git('rev-parse', 'HEAD').decode().strip()
                def check():
                    if lab == 6:
                        lab06_reporting._committed_inputs(report, collection, head)
                    else:
                        with patch.object(lab07_reporting, 'DEFAULT_CORPUS', corpus):
                            lab07_reporting._committed_inputs(report, head)
                check()
                text.write_bytes(b'{"value": 1}\r\n')
                self.assertEqual(git('diff', 'HEAD', '--', str(text)), b'')
                check()
                text.write_bytes(b'{"value": 2}\r\n')
                with self.assertRaises(WorkflowError):
                    check()
                text.write_bytes(b'{"value": 1}\r\n')
                binary.write_bytes(b'\x00PNG\nbytes\n')
                with self.assertRaises(WorkflowError):
                    check()
                binary.write_bytes(b'\x00PNG\r\nbytes\n')
                text.unlink()
                from learning_project.committed_inputs import matches_committed_file
                self.assertFalse(matches_committed_file(root, text, head))
                text.write_bytes(b'{"value": 1}\r\n')
                git('config', 'core.autocrlf', 'false')
                with self.assertRaises(WorkflowError):
                    check()
                git('config', 'core.autocrlf', 'true')
                extra = report / 'untracked.json'
                extra.write_bytes(b'{}\n')
                with self.assertRaises(WorkflowError):
                    check()
                extra.unlink()
                text.write_bytes(b'{"value": 2}\r\n')
                git('add', str(text))
                with self.assertRaises(WorkflowError):
                    check()


if __name__ == '__main__':
    unittest.main()
