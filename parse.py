

import os
import re
import pandas as pd
from threading import Thread

from github import Github

# using an access token
g = Github(os.environ['GITHUB_ACCESS_TOKEN'])


def extract_repo(url):
    reu = re.compile('^https://github.com/([\w-]+/[-\w\.]+)$')
    return m.group(1) if (m := reu.match(url)) else ''


def get_last_commit(repo):
    try:
        if not repo:
            return ''
        r = g.get_repo(repo)
        cs = r.get_commits()
        return cs[0].commit.author.date.strftime('%Y-%m-%d')
    except:
        print('ERROR' + repo)
        return 'error'


class Project(Thread):

    def __init__(self, match, section):
        super().__init__()
        self._match = match
        self.regs = None
        self._section = section

    def run(self):
        m = self._match
        is_github = 'github.com' in m.group(2)
        is_cran = 'cran.r-project.org' in m.group(2)
        repo = extract_repo(m.group(2))
        last_commit = get_last_commit(repo)
        self.regs = dict(
            project=m.group(1),
            section=self._section,
            last_commit=last_commit,
            url=m.group(2),
            description=m.group(3),
            github=is_github,
            cran=is_cran,
            repo=repo
        )


projects = []

with open('README.md', 'r', encoding='utf8') as f:
    ret = re.compile('^(#+) (.*)$')
    rex = re.compile('^\s*- \[(.*)\]\((.*)\) - (.*)$')
    m_titles = []
    last_head_level = 0
    for line in f:
        if m := rex.match(line):
            p = Project(m, ' > '.join(m_titles[1:]))
            p.start()
            projects.append(p)
        elif m := ret.match(line):
            hrs = m[1]
            if len(hrs) <= last_head_level:
                for _ in range(last_head_level - len(hrs) + 1):
                    m_titles.pop()
            m_titles.append(m[2])
            last_head_level = len(hrs)

while True:
    checks = [not p.is_alive() for p in projects]
    if all(checks):
        break

projects = [p.regs for p in projects]
df = pd.DataFrame(projects)
df.to_csv('projects.csv', index=False)
df.to_markdown('projects.md', index=False)
