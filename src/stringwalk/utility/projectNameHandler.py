from importlib import metadata


def getProjectName():
    try:
        dist = metadata.distribution('stringwalk')
        return dist.metadata["Name"]
    except metadata.PackageNotFoundError:
        raise Exception("Package not found or installed")

def getProjectNameLower():
    result = getProjectName().lower()
    return result