FROM python:3.12-slim-bookworm
WORKDIR /repo
COPY tests/requirements.txt /tmp/test-requirements.txt
RUN pip install --no-cache-dir -r /tmp/test-requirements.txt
COPY pytest.ini ./
COPY tests ./tests
COPY encore/app ./encore/app
COPY investigation/crew_support.py ./investigation/crew_support.py
COPY proxy ./proxy
COPY traffic ./traffic
COPY scripts ./scripts
CMD ["python", "tests/run_stack.py"]
