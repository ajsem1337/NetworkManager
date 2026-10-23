"""Build PowerShell calls without cmd.exe or executable user input."""


def powershell(script):
    return ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script]


def literal(value):
    """Quote a PowerShell single-quoted string, including embedded apostrophes."""
    if not value or any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError('Nieprawidłowa nazwa karty')
    return "'" + value.replace("'", "''") + "'"
