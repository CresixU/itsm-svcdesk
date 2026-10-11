<!-- ai-generated: 90% - Claude Code wrote the explanation from the numbers the checker's own load command printed; the author reviews it -->
# The gap between what the client sees and what svcdesk's histogram says

**Setup.** Toxiproxy 2.12.0 sits in front of `svcdesk` (compose profile `gap`). The proxy `svcdesk` listens on 8666 and
forwards to `svcdesk:8080`; its one toxic is a downstream `latency` of 100 ms with 10 ms of jitter. Two calls to its API on
8474 create it (`POST /proxies` with `{"name": "svcdesk", "listen": "0.0.0.0:8666", "upstream": "svcdesk:8080", "enabled":
true}`, then `POST /proxies/svcdesk/toxics` with `{"type": "latency", "stream": "downstream", "toxicity": 1.0, "attributes":
{"latency": 100, "jitter": 10}}`). I measured with `itsmlab load 3 --base-url http://host.docker.internal:8666` (the M-08
load: 60 s open-loop at 40 requests/s, latency-corrected).

**The numbers.** The client's p99 (oha, through the proxy) was 198.9 ms; the server's p99, `histogram_quantile(0.99)` over
the increments of `http_server_request_duration_seconds` for `/kb/search` during the same run, was 92.3 ms; the gap is 106.6
ms. Without the toxic the same two numbers agree within a millisecond or two (q 94.7 ms, histogram 94.6 ms), and the median
moves the same way: 16.7 ms without the toxic, 122.3 ms through it.

**Why the gap is about 107 ms and not exactly 100.** `svcdesk`'s timer starts when the request enters the application
and stops when the response is handed to the server, so it cannot see anything that happens after it: the toxic holds every
response for 100 ms (give or take the jitter) *after* `svcdesk` has already recorded a perfectly normal 92 ms, and the client
adds that wait to the time it measures. The extra 6 ms or so over the nominal 100 comes from three smaller things: the client
p99 is the top of a sum of two random delays, the slow mode of `kb-index` and the upper end of the jitter (up to +10 ms), so
its tail sits above 100 ms of toxic by most of the jitter; there is a second hop, the proxy, with its own connection and copy
costs; and the server's p99 is an interpolation inside the 5 ms bucket (0.09, 0.095], not an exact value.

**What it means.** A white-box histogram measures the server, not the user. A dashboard or an SLO built only on it would
show a healthy p99 of 92 ms while every user waits twice that, and nothing in `svcdesk` would ever fire an alert for a
slow network, a loaded proxy or a load balancer. The latency SLI of `slo.md` (threshold 0.15 s) is therefore a statement
about the service, and an edge or black-box measurement is still needed for what the person at the desk experiences.
