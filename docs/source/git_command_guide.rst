.. Restructured Text (RST) Syntax Primer: http://sphinx-doc.org/rest.html


#####################################
Git Command Reference
#####################################



Tutorials
=========================

https://www.atlassian.com/git/tutorials

https://try.github.io/levels/1/challenges/1

https://help.github.com/articles/good-resources-for-learning-git-and-github/


Command summary
============================================

| ``git clone <URL>`` - clone a local copy of a remote repo in a new directory
| ``git remote`` - manage remote repo names (e.g. “origin”) and URLs
| ``git fetch <remote>`` - fetch updates from remote repo
| ``git push <remote> <branch>`` - push current local branch to remote branch
| ``git merge <branch>`` or ``git merge <remote>/<branch>`` - merge updates from local or remote branch into current local branch
| ``git branch`` - manage branches in local and remote repos
| ``git checkout <branch>`` - switch to a different local branch
| ``git add`` - add files to the index
| ``git commit`` - commit changes to the local branch
| ``git status`` - view status of working directory
| ``git log`` - view commit log of current local branch
| ``git diff`` - view differences between working directory and index



Detailed command reference
==================================================


Initiate or clone a repository
---------------------------------------------

Clone a local copy of a repository (repo) in a new directory (remote repo is the “origin” remote)::

    % git clone <URL>

Initiate a repository in the current directory::

    % git init


Interacting with the remote repo
---------------------------------------------

List remotes and URLs (omitting -v lists only remote names, not URLs)::

    % git remote -v

Add a remote repo, such as “upstream” (good for the parent of a forked repo)::

    % git remote add <new-remote> <URL>

Fetch updates from a remote repo, such as “origin” (note that fetch does not merge anything into the local repo)::

    % git fetch <remote>

List remote branches::

    % git branch -r

Merge remote branch into current branch::

    % git merge <remote>/<branch>

Push local branch to remote repo::

    % git push <remote> <branch>

Delete remote branch::

    % git push <remote> --delete <branch>



Working within the local repo
---------------------------------------------

List local branches::

    % git branch

Create new branch from master branch in local repo::

    % git branch <new branch>

Create new branch from existing branch in local repo::

    % git branch <new branch> <existing branch>

Delete local branch::

    % git branch -d <branch>

Checkout (switch) to different local branch (or create local version of remote branch if local branch does not exist)::

    % git checkout <branch>

Merge local branch into current branch::

    % git merge <branch>

Update index with any new/deleted/moved files::

    % git add -A

Commit changes in current branch::

    % git commit -a -m “message”

View differences with index::

    % git diff

View differences with another branch::

    % git diff <target branch>

View commit log for cirrent branch::

    % git log

View status of working directory::

    % git status





