import compas.geometry


def rhino_transform_to_matrix(T):
    # type: (Rhino.Geometry.Transform) -> list[list[float]]
    """Convert :class:`Rhino.Geometry.Transform` to transformation matrix.

    Parameters
    ----------
    T : :class:`Rhino.Geometry.Transform`

    Returns
    -------
    :class:`list` of :class:`list` of :class:`float`.
    """
    M = [[T.Item[i, j] for j in range(4)] for i in range(4)]
    return M


def transform_to_compas(T):
    # type: (Rhino.Geometry.Transform) -> compas.geometry.Transform
    """Convert :class:`Rhino.Geometry.Transform` to :class:`compas.geometry.Transformation`.

    Parameters
    ----------
    T : :class:`Rhino.Geometry.Transform`

    Returns
    -------
    :class:`compas.geometry.Transformation`
    """  # noqa: E501
    M = rhino_transform_to_matrix(T)
    return compas.geometry.Transformation(matrix=M)
