#!/usr/bin/env bash
set -ev

bin_dir='/usr/local/bin'

# Dependencies.

  sudo apt-get update
  sudo apt-get install -y build-essential bison curl git haskell-platform lua5.1 libglib2.0-dev mercurial unzip

  # go
  # Requires: mercurial, bison.
  if [ ! -f "$HOME/.gvm/scripts/gvm" ]; then
    bash < <(curl -LSs 'https://raw.githubusercontent.com/moovweb/gvm/master/binscripts/gvm-installer')
  fi
  . "$HOME/.gvm/scripts/gvm"
  gvm install 'go1.2.2'
  gvm use 'go1.2.2' --default

  # haskell
  printf '\n%s\n' 'export PATH="$PATH:$HOME/.cabal/bin"' >> "$HOME/.profile"
  cabal update

  # nodejs
  VERSION='0.10.26'
  curl 'https://raw.githubusercontent.com/creationix/nvm/v0.7.0/install.sh' | sh
  . "$HOME/.nvm/nvm.sh"
  echo '. "$HOME/.nvm/nvm.sh"
  nvm use "'"$VERSION"'" &>/dev/null
  ' >> "$HOME/.bashrc"
  nvm install "$VERSION"

  # python pip
  wget -O- https://bootstrap.pypa.io/get-pip.py | sudo python

  # ruby
  curl -L https://get.rvm.io | bash -s stable
  . "$HOME/.rvm/scripts/rvm"
  rvm install 2.1.1

# Engines.

  # blackfriday
  # TODO: use latest stable version.
  go get 'github.com/russross/blackfriday'
  go get 'github.com/russross/blackfriday-tool'

  # hoedown
  dir='hoedown'
  cd '/tmp'
  git clone 'https://github.com/hoedown/hoedown' "$dir"
  cd "$dir"
  git checkout "$(git describe --tags --abbrev=0)"
  make
  sudo mv 'hoedown' "$bin_dir"
  cd '..'
  rm -rf -- "$dir"

  # kramdown
  gem install 'kramdown'

  # lunamark
  ## TODO get working. 'alt_getopt' not found.
  #dir='lunamark'
  #cd '/tmp'
  #git clone 'https://github.com/jgm/lunamark' "$dir"
  #cd "$dir"
  ## TODO use latests stable version.
  ##git checkout "$(git describe --tags --abbrev=0)"
  #make standalone
  #sudo mv 'lunamark' "$bin_dir"
  #cd '..'
  #rm -rf -- "$dir"

  # markdwn_pl
  dir='Markdown_1.0.1'
  zip="${dir}.zip"
  cd '/tmp'
  wget -O "${zip}" 'http://daringfireball.net/projects/downloads/Markdown_1.0.1.zip'
  unzip "${zip}"
  sudo mv "${dir}/Markdown.pl" "$bin_dir"
  rm -rf -- "$dir" "$zip"

  # markdown2
  sudo pip install 'markdown2'

  # marked
  npm install -g 'marked'

  # maruku
  gem install 'maruku'

  # md2html
  npm install -g 'markdown'

  # multimarkdown
  dir='MultiMarkdown-4'
  cd '/tmp'
  git clone --recursive 'https://github.com/fletcher/MultiMarkdown-4' "$dir"
  cd "$dir"
  git checkout "$(git describe --tags --abbrev=0)"
  make
  sudo make install
  cd '..'
  rm -rf -- "$dir"

  # pandoc
  cabal install 'pandoc'

  # peg-markdown
  # Requires: libglib2.0-dev.
  dir='peg-markdown'
  cd '/tmp'
  git clone 'https://github.com/jgm/peg-markdown' "$dir"
  cd "$dir"
  git checkout "$(git describe --tags --abbrev=0)"
  make
  sudo mv 'markdown' "${bin_dir}/peg-markdown"
  cd '..'
  rm -rf -- "$dir"

  # rdiscount
  gem install 'rdiscount'

  # redcarpet
  gem install 'redcarpet'

  # showdown
  npm install -g 'showdown'

# Required or else Karmdown and Maruku raise UTF-8 exceptions.
# with the default `LC_ALL=en_US`.
printf '\n%s\n' 'export LC_ALL=""' >> "$HOME/.profile"

printf '\n%s\n' 'cd /vagrant' >> "$HOME/.bashrc"
