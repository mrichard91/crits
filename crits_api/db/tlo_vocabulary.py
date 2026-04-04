"""Default vocabulary values used by modern GraphQL TLO queries."""

DEFAULT_DOMAIN_RECORD_TYPES = ("A", "AAAA", "CNAME", "MX", "NS", "PTR", "SOA", "SRV", "TXT")

DEFAULT_IP_TYPES = (
    "IPv4 Address",
    "IPv4 Subnet",
    "IPv6 Address",
    "IPv6 Subnet",
)

DEFAULT_EVENT_TYPES = (
    "Application Compromise",
    "Denial of Service",
    "Distributed Denial of Service",
    "Exploitation",
    "Intel Sharing",
    "Malicious Code",
    "Phishing",
    "Privileged Account Compromise",
    "Scanning",
    "Sensor Alert",
    "Social Engineering",
    "Sniffing",
    "Spam",
    "Strategic Web Compromise",
    "Unauthorized Information Access",
    "Unknown",
    "Website Defacement",
)
