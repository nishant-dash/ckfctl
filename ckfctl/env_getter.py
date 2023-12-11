from os import getenv

def get_env_proxy_vars() -> {}:
    env_dict = {}
    for i in ["http_proxy", "https_proxy", "no_proxy"]:
        env_dict[i] = getenv(i)
        env_dict[i.upper()] = getenv(i.upper())
    return env_dict

if __name__ == "__main__":
    from rich.console import Console
    console = Console()
    console.print(get_env_proxy_vars())