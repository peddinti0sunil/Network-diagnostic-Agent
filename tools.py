import subprocess
import platform
import socket
import httpx
from langchain_core.tools import tool

@tool
def ping_host(host: str) -> str:
    """
    Use this tool to check if a host is reachable by pinging it.
    Pass a domain name or IP address as input.
    Returns the reachability status and response latency.
    """
    
    flag = "-n" if platform.system().lower() == "windows" else "-c"

    result = subprocess.run(
        ["ping", flag, "4", host],
        capture_output=True,
        text=True,
        timeout=10  # timeout after 10 seconds to avoid hanging
    )
    
    if result.returncode == 0:
        return f"Host {host} is reachable. Response:\n{result.stdout}"
    else:
        return f"Host {host} is not reachable. or not responding. Error:\n{result.stdout}"

@tool
def scan_port(host: str) -> str:
    """
    Use this tool to check if a specific port on a host is open.
    Pass a domain name or IP address  as input.
    Returns the status of the port (open/closed).
    """
    ports = {
        80: "HTTP",
        443: "HTTPS",
        22: "SSH",
        21: "FTP",
        3306: "MySQL",
        3389: "RDP"
    }

    open_ports = []
    for port, service in ports.items():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(3)  # timeout after 3 seconds
            result = sock.connect_ex((host, port))
            if result == 0:
                open_ports.append(f"Service:{service} (port {port}) is open")
    if open_ports:
        return f"Host {host} has the following open ports:\n" + "\n".join(open_ports)
    
    return f"Host {host} has no common open ports."


@tool      
def dns_lookup(host: str) -> str:
    """
    Use this tool to perform a DNS lookup for a given host.
    Pass a domain name as input.
    Returns the resolved IP address(es) for the domain.
    """
    try:
        ip_addresses = socket.gethostbyname_ex(host)[2]
        return (f"DNS lookup for {host} returned the following IP addresses:\n" + "\n".join(ip_addresses))
    except socket.gaierror as e:
        return (
            f"DNS lookup failed for {host}. "
            f"Caught error{e}."
        )
    

@tool
def check_website(url: str) -> str:
    """
    Use this tool to check whether a website is accessible and responding correctly.
    Pass a full website URL as input.
    Returns the HTTP status code, response time, and overall health status of the website.
    """

    try:
        response = httpx.get(
            url,
            timeout=5,
            follow_redirects=True
        )

        status_code = response.status_code

        response_time = response.elapsed.total_seconds()

        if 200 <= status_code < 300:
            health_status = "healthy"

        elif 300 <= status_code < 400:
            health_status = "redirected"

        elif 400 <= status_code < 500:
            health_status = "client error"

        elif 500 <= status_code < 600:
            health_status = "server error"

        else:
            health_status = "unknown"

        

        return (
            f"Website check results for {url}:\n"
            f"Status Code: {status_code}\n"
            f"Response Time: {response_time:.2f} seconds\n"
            f"Health Status: {health_status}"
        )

    except httpx.HTTPError as e:

        return (
            f"Failed to connect to {url}. "
            f"Caught error: {str(e)}"
        )



ALL_TOOLS = [ping_host, scan_port,dns_lookup,check_website]

if __name__ == "__main__":
    # Example usage
    print(check_website.invoke({"url": "https://google.com"}))