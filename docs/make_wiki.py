import os
import sphinx

if __name__ == '__main__':
    sphinx.build_main(['sphinx-build', '-a', '-b', 'rst', 'source', os.path.join('..', '..', 'bi_etl_wiki')])
