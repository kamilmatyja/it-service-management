<!-- ai-generated: 0% - Hand-written -->
# Latency Gap Explanation

The client-server latency gap represents the time a request spends in transit between the client and the server's application code, which the server's internal monitoring cannot observe. In our setup, this gap is introduced by a Toxiproxy latency toxic adding approximately 100ms of delay.
When the client measures the latency, it includes this network delay. However, the server's Prometheus histogram only measures execution time. This demonstrates why relying solely on server-side metrics is insufficient for understanding user experience.