#!/usr/bin/env python3
from subprocess import Popen, PIPE
import logging as l
import os
from pathlib import Path
from shutil import copytree, rmtree
from datetime import datetime

_LANGUAGES = [
        "bash",
        "bibtex",
        "c",
        "cpp",
        "c_sharp",
        "cmake",
        "css",
        "dockerfile",
        "dot",
        "html",
        "javascript",
        "json",
        "latex",
        "lua",
        "luadoc",
        "make",
        "markdown",
        "ninja",
        "python",
        "r",
        "robot",
        "rust",
        "scala",
        "scss",
        "toml",
        "vim",
        "vimdoc",
]


def _loglevel() -> int:
    if n := os.environ.get("LOG"):
        c = n.upper()[0]
        if c == "D":
            return l.DEBUG
        elif c == "I":
            return l.INFO
        elif c == "W":
            return l.WARN
        elif c == "E":
            return l.ERROR
    return l.INFO


def backup_config():
    l.info("making backup of current configuration ...")
    if xdg_config_home := os.environ.get("XDG_CONFIG_HOME"):
        cfgroot = Path(xdg_config_home).absolute()
    else:
        l.warning("XDG_CONFIG_HOME is not set, assuming $HOME/.config")
        cfgroot = Path("~/.config").expanduser().absolute()
    nvim_cfgroot = cfgroot / "nvim"
    if nvim_cfgroot.exists():
        backupdir = cfgroot / "nvim-jk" / datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        copytree(src=nvim_cfgroot, dst=backupdir)
        l.info(f"saved backup of config in {backupdir}")
        rmtree(nvim_cfgroot)
    else:
        l.warning(f"nvim configuration not found in {nvim_cfgroot}, no backup made")


def install_plug():
    l.info("installing vim-plug ...")
    vimplugdir = os.environ.get("XDG_DATA_HOME") or Path("~/.local/share").expanduser().absolute()
    dst = vimplugdir / 'nvim' / 'site' / 'autoload' / 'plug.vim'
    if dst.exists():
        l.info(f"vim-plug is already installed in {dst}, skipping")
        return
    p = Popen(
        [
            "curl",
            "-fLo",
            dst,
            "--create-dirs",
            "https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim",
        ],
    )
    _ = p.communicate()
    if p.wait() == 0:
        l.info(f"installed vim-plug in {dst}!")
    else:
        raise RuntimeError("could not install vim-plug, see log")


def write_init_lua():
    base = """
local Plug = vim.fn['plug#']

vim.call('plug#begin', '~/.config/nvim/plugged')

Plug('tpope/vim-sensible')
Plug('scrooloose/NERDTree', {on = 'NERDTreeToggle'})
Plug('junegunn/tabularize')
Plug('nvim-lualine/lualine.nvim')
Plug('nvim-tree/nvim-web-devicons')
Plug('nvim-treesitter/nvim-treesitter', {['do'] = vim.fn['TSUpdateSync']})

vim.call('plug#end')
    """

    ext = """
require('nvim-treesitter.configs').setup {
    highlight = {
        enable = on,
        autoinstall = on,
    }
}

require('lualine').setup {
    options = {
       section_separators = { left = '', right = '' },
       component_separators = { left = '', right = '' }
    }
}
    """

    cfgdir = Path("~/.config/nvim").expanduser().absolute()
    cfgdir.mkdir(parents=True, exist_ok=True)
    with open(cfgdir / "init.lua", "w+") as f:
        f.write(base)
    l.info(f"wrote configuration to {cfgdir / 'init.lua'}")

    p = Popen(['nvim', '-c', 'PlugUpgrade | PlugUpdate | qa'])
    _ = p.communicate()
    if p.wait() != 0:
        raise RuntimeError("initial plugin installation failed!")

    with open(cfgdir / "init.lua", "a") as f:
        f.write(ext)
    l.info(f"wrote extended configuration to {cfgdir / 'init.lua'}")
   
    l.info("installing language parsers, this may take a while ...")
    p = Popen(['nvim', '--headless', '-c', 'TSInstallSync ' + ' '.join(_LANGUAGES) + ' | qa'], stdout=PIPE)
    _ = p.communicate()
    if p.wait() != 0:
        raise RuntimeError("initial language installations failed!")

    l.info("neovim configured, check it out via 'nvim'")


if __name__ == "__main__":
    l.basicConfig(level=_loglevel())
    backup_config()
    install_plug()
    write_init_lua()
