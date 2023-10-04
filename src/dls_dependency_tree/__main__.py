from dls_dependency_tree import dependency_checker

__all__ = ["main"]


def main():
    dependency_checker.dependency_checker()


# test with: python -m dls_launcher_app
if __name__ == "__main__":
    main()
