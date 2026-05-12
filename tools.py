import subprocess
import platform
import socket
import httpx
from langchain_core.tools import tool
import nmap

@tool
def ping_host(host: str) -> str:
    """
    Use this tool to check if a host is reachable by pinging it.
    Pass a domain name or IP address as input.
    Returns the reachability status and response latency.
    """
    
    flag = "-n" if platform.system().lower() == "windows" else "-c"
    try:
        result = subprocess.run(
            ["ping", flag, "4", host],
            capture_output=True,
            text=True,
            timeout=20  # timeout after 10 seconds to avoid hanging
        )
        
        if result.returncode == 0:
            return f"Host {host} is reachable. Response:\n{result.stdout}"
        else:
            return f"Host {host} is not reachable. or not responding. Error:\n{result.stdout}"
    except subprocess.TimeoutExpired:
        return f"Ping command timed out while trying to reach {host}."
    except Exception as e:
        return f"An error occurred while trying to ping {host}. Error: {str(e)}"


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


@tool
def nmap_scan(host: str) -> str:
    """
    Use this tool to perform a basic nmap scan on a given host.
    Pass a domain name or IP address as input.
    Returns the open ports and services detected by nmap.
    """
    nm = nmap.PortScanner()
    try:
        nm.scan(host, arguments='-sV -T4 --open')
        if nm.all_hosts():
            scanned_host = nm.all_hosts()[0]
            open_ports = []
            for proto in nm[scanned_host].all_protocols():
                lport = nm[scanned_host][proto].keys()
                for port in lport:
                    state = nm[scanned_host][proto][port]['state']
                    service = nm[scanned_host][proto][port]['name']
                    product = nm[scanned_host][proto][port]['product']
                    info = f"{service} {product}".strip()
                    if state == 'open':
                        open_ports.append(f"Port {port}/{proto} is open (Service: {service}) info: {info})")
            if open_ports:
                return f"Nmap scan results for {host}:\n" + "\n".join(open_ports)
            else:
                return f"Nmap scan results for {host}: No open ports found."
        else:
            return f"Nmap scan failed for {host}. Host not found."
    except Exception as e:
        return f"An error occurred during nmap scan for {host}. Error: {str(e)}"
    
ALLOWED_COMMANDS = [
    "ping",
    "nslookup",
    "tracert",
    "netstat",
    "ipconfig"
]
# dangerous characters that chain commands
DANGEROUS_CHARS = ["&", "|", ";", ">", "<", "`"]

@tool
def shell_tool(command: str) -> str:
    """
    Run a safe network diagnostic command in the terminal.
    Only these commands are allowed: ping, nslookup, tracert, netstat, ipconfig.
    Pass the full command as a string, for example:
    'nslookup google.com'
    """

    try:

        parts = command.strip().split()

        if not parts:
            return "No command provided."

        base_command = parts[0].lower()

        if base_command not in ALLOWED_COMMANDS:

            return (
                f" Command '{base_command}' is not allowed.\n"
                f"Allowed commands: {', '.join(ALLOWED_COMMANDS)}"
            )
        if any(char in command for char in DANGEROUS_CHARS):
            return (
                f" Command contains dangerous characters that are not allowed.\n"
                f"Please avoid using characters like: {' '.join(DANGEROUS_CHARS)}"
            )

        result = subprocess.run(
            parts,
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode == 0:

            return (
                f" Command executed successfully.\n\n"
                f"COMMAND:\n{command}\n\n"
                f"OUTPUT:\n{result.stdout}"
            )

        return (
            f" Command executed with errors.\n\n"
            f"COMMAND:\n{command}\n\n"
            f"ERROR OUTPUT:\n{result.stderr}"
        )

    except subprocess.TimeoutExpired:

        return (
            f" Command timed out after 15 seconds:\n"
            f"{command}"
        )

    except Exception as e:

        return (
            f" Failed to execute command.\n"
            f"Error: {str(e)}"
        )

ALL_TOOLS = [ping_host, scan_port,dns_lookup,check_website, nmap_scan,shell_tool]

if __name__ == "__main__":
    # Example usage
    print(check_website.invoke({"url": "https://google.com"}))