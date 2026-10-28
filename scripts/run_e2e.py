"""Run browser acceptance against isolated local SQLite data and local servers.
Install Chromium with `cd frontend && npx playwright install chromium` first.
Optional PLAYWRIGHT_CHROMIUM_EXECUTABLE selects an already installed browser.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import time
from urllib.request import urlopen

root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='datastraw-e2e-') as directory:
    env={**os.environ,'DATABASE_URL':f'sqlite:///{directory}/workspace.db'}
    # Tests use an isolated workspace; an inherited production write token is irrelevant.
    env.pop('ADMIN_TOKEN',None)
    subprocess.run(['python','-m','app.seed'],cwd=root,env=env,check=True)
    with open(Path(directory)/'servers.log','w+') as logs:
        processes=[subprocess.Popen(['python','-m','uvicorn','app.main:app','--port','8000'],cwd=root,env=env,stdout=logs,stderr=logs),subprocess.Popen(['node','node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','5173'],cwd=root/'frontend',env=env,stdout=logs,stderr=logs)]
        try:
            for url in ['http://127.0.0.1:8000/health','http://127.0.0.1:5173']:
                for attempt in range(100):
                    if any(p.poll() is not None for p in processes): raise RuntimeError('Test server exited; ensure ports 8000/5173 are free')
                    try:
                        with urlopen(url,timeout=1): break
                    except OSError: time.sleep(.1)
                else: raise RuntimeError(f'Test server did not become ready: {url}')
            result=subprocess.run(['npx','playwright','test'],cwd=root/'frontend',env=env)
            if result.returncode:
                logs.flush();logs.seek(0);print(logs.read()[-5000:])
            raise SystemExit(result.returncode)
        finally:
            for p in processes:
                p.terminate()
            for p in processes:
                try:p.wait(timeout=5)
                except subprocess.TimeoutExpired:p.kill()
