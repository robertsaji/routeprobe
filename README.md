# routeprobe

A minimal HTTP route testing framework that validates API contracts from a YAML spec.

---

## Installation

```bash
pip install routeprobe
```

---

## Usage

Define your API contract in a YAML spec file:

```yaml
# routes.yaml
base_url: https://api.example.com
routes:
  - path: /users
    method: GET
    expect:
      status: 200
      json:
        type: array

  - path: /users/1
    method: GET
    expect:
      status: 200
      json:
        id: 1
```

Then run the probe against your spec:

```bash
routeprobe run routes.yaml
```

Or use it programmatically:

```python
from routeprobe import Probe

probe = Probe("routes.yaml")
results = probe.run()
results.summary()
```

---

## Output

```
✔  GET /users          200 OK
✔  GET /users/1        200 OK
✘  POST /users         expected 201, got 422

2 passed, 1 failed
```

---

## License

MIT © routeprobe contributors