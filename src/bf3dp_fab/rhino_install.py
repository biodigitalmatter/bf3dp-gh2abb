import compas.plugins


@compas.plugins.plugin(category="install")
def installable_rhino_packages():
    return ["bf3dp_fab"]
