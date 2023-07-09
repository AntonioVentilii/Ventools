import git


def init_submodules():
    """Initialize all submodules if not already initiated."""
    repo = git.Repo(".")
    submodules = repo.submodules
    if len(submodules) == 0:
        print("No submodules found.")
        return

    initiated_submodules = []
    for submodule in submodules:
        if submodule.module_exists():
            initiated_submodules.append(submodule.path)

    if len(initiated_submodules) == 0:
        print("No submodules are initiated. Initializing all submodules...")
        repo.submodule_update(init=True)
    else:
        print("The following submodules are already initiated:")
        for submodule_path in initiated_submodules:
            print(f"- {submodule_path}")


def checkout_submodule_branch():
    """Checkout the branch specified in .gitmodules for each submodule."""
    repo = git.Repo(".")
    submodules = repo.submodules
    for submodule in submodules:
        path = submodule.path
        branch = submodule.config_reader().get_value("branch")
        if not branch:
            print(f"Branch not specified for submodule: {path}")
            continue

        submodule_repo = submodule.module()
        current_branch = submodule_repo.active_branch.name
        if current_branch != branch:
            try:
                submodule_repo.git.diff("--quiet", "HEAD")
                submodule_repo.git.checkout(branch)
            except git.GitCommandError:
                choice = input(
                    f"Submodule '{path}' has local changes. Do you want to checkout '{branch}' branch anyway? (y/n): ")
                if choice.lower() == 'y':
                    submodule_repo.git.checkout(branch)
            else:
                print(f"Checked out branch '{branch}' for submodule: {path}")
        else:
            print(f"Submodule '{path}' already on branch '{branch}'")


def pull_submodule_branch():
    """Pull the branch for each submodule."""
    repo = git.Repo(".")
    submodules = repo.submodules
    for submodule in submodules:
        path = submodule.path
        branch = submodule.config_reader().get_value("branch")
        if branch:
            try:
                submodule.repo.git.pull("origin", branch)
            except git.GitCommandError:
                print(f"Failed to pull branch '{branch}' for submodule: {path}")
            else:
                print(f"Pulled branch '{branch}' for submodule: {path}")


if __name__ == "__main__":
    init_submodules()
    checkout_submodule_branch()
    pull_submodule_branch()
