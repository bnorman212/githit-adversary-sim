FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -e .
ENV I_UNDERSTAND_AND_HAVE_PERMISSION=YES
CMD ["adversary-sim", "--config", "examples/config.lab.json"]
