"""Data representation of discrete fabrication elements."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import compas.datastructures
from compas.data import Data
import compas.geometry as cg

try:
    import Rhino.Geometry as rg
    from compas_rhino.conversions import point_to_rhino

    import typing

    if typing.TYPE_CHECKING:
        from compas_fab.robots import Configuration  # noqa: F401

except ImportError:
    pass


class FabricationElement(Data):
    """Describes a fabrication element in fabrication processes

    Adapted from Rapid Clay Formations (https://github.com/gramaziokohler/rapid_clay_formations_fab/blob/3eb4e441264f7881e33927df09fcb39b7d3de656/src/rapid_clay_formations_fab/fab_data/fabrication_element.py)

    The element is assumed to be spherical.

    Parameters
    ----------
    location_frame
        Location to place element
    egress_frame
        Frame to travel to before and after placing element
    radius
        The radius of the initial element.
    entry_trajectory
        Trajectory to execute to get to egress_frame, optional.
    exit_trajectory
        Trajectory to execute to get from egress_frame, optional.
    placed_isotimestamp
        Time of placement in formatted according to
    """

    def __init__(
        self,
        location_frame,  # type: cg.Frame
        entry_frame, # type: cg.Frame
        exit_frame,# type: cg.Frame
        entry_trajectory=None,  # type: [Configuration] | None
        exit_trajectory=None,  # type: [Configuration] | None
        placed_isotimestamp=None,  # type: int | None
        **kwargs  # fmt: skip
    ):
        placed_isotimestamp = kwargs.pop("placed_isotimestamp", None)
        entry_trajectory = kwargs.pop("entry_trajectory", None)
        exit_trajectory = kwargs.pop("exit_trajectory", None)
        super(FabricationElement, self).__init__(**kwargs)

        self.location_frame = location_frame
        self.entry_frame = entry_frame
        self.exit_frame = exit_frame
        self.entry_trajectory = entry_trajectory
        self.exit_trajectory = exit_trajectory
        self.placed_isotimestamp = placed_isotimestamp

    def __repr__(self):
        return "FabricationElement({}, {}, {}, {}, {}, {})".format(
            self.location_frame,
            self.entry_frame,
            self.exit_frame,
            self.entry_trajectory,
            self.exit_trajectory,
            self.placed_isotimestamp,
        )

    @property
    def data(self):  # type: () -> dict
        """:obj:`dict` : The data dictionary that represents the :class:`FabricationElement`."""  # noqa: E501
        return {
            "location_frame": self.location_frame,
            "entry_frame": self.entry_frame,
            "exit_frame": self.exit_frame,
            "entry_trajectory": self.entry_trajectory,
            "exit_trajectory": self.exit_trajectory,
            "placed_isotimestamp": self.placed_isotimestamp,
        }

    @data.setter
    def data(self, data):  # type: (dict) -> None
        self.location_frame = data["location_frame"]
        self.entry_frame = data["entry_frame"]
        self.exit_frame = data["exit_frame"]
        self.entry_trajectory = data["entry_trajectory"]
        self.exit_trajectory = data["exit_trajectory"]
        self.placed_isotimestamp = data["placed_isotimestamp"]

    @classmethod
    def from_data(cls, data):
        return cls(
            data["location_frame"],
            data["entry_frame"],
            data["exit_frame"],
            entry_trajectory=data["entry_trajectory"],
            exit_trajectory=data["exit_trajectory"],
            placed_isotimestamp=data["placed_isotimestamp"],
        )

    def _get_defining_geometries(self):
        return (self.location_frame, self.entry_frame, self.exit_frame)

    def transform(self, xform):  # type: (compas.geometry.Transformation) -> None
        for geo in self._get_defining_geometries():
            geo.transform(xform)

    def transformed(
        self, xform
    ):  # type: (compas.geometry.Transformation) -> FabricationElement
        new_instance = self.copy()
        new_instance.transform(xform)
        return new_instance

    @staticmethod
    def rotate_frame_around_self(frame, rx, ry, rz):
        rot_constructor = cg.Rotation.from_axis_and_angle

        Rx = rot_constructor(frame.xaxis, rx, point=frame.point)
        Ry = rot_constructor(frame.yaxis, ry, point=frame.point)
        Rz = rot_constructor(frame.zaxis, rz, point=frame.point)

        # got an error when I multiplied. Probably stupid way of doing this
        frame.transform(Rx)
        frame.transform(Ry)
        frame.transform(Rz)

    def rotate_around_self(self, rx, ry, rz):  # type: (float, float, float) -> None
        for geo in self._get_defining_geometries():
            if isinstance(geo, cg.Frame):
                self.rotate_frame_around_self(geo, rx, ry, rz)

    def rotated_around_self(
        self, rx, ry, rz
    ):  # type: (float, float, float) -> FabricationElement
        new_instance = self.copy()
        new_instance.rotate_around_self(rx, ry, rz)
        return new_instance

    # Derived data points
    #####################

    def get_circle(self, radius):
        """Get :class:`compas.geometry.Circle` representing fabrication element.

        Returns
        -------
        :class:`compas.geometry.Circle`
        """
        plane = cg.Plane(self.location_frame.point, self.location_frame.normal)
        return cg.Circle(plane, radius)

    def get_sphere(self, radius):
        """Get :class:`compas.geometry.Sphere` representing of fabrication element.

        Returns
        -------
        :class:`compas.geometry.Sphere`
        """
        return cg.Sphere(self.location_frame.point, radius)

    def get_cgmesh(self, radius, u=8, v=4):
        """Generate mesh representation of bullet with custom resolution.

        Parameters
        ----------
        u, optional
            Number of faces in the around direction. Defaults to 8.
        v, optional
            Number of faces in the top-to-bottom direction. Defaults to 4.

        Returns
        -------
        :class:`compas.geometry.datastructures.Mesh`
        """
        sphere = self.get_sphere(radius)
        vertices, faces = sphere.to_vertices_and_faces(u=u, v=v)
        return compas.datastructures.Mesh.from_vertices_and_faces(vertices, faces)

    # Construct geometrical representations of object using :any:`Rhino.Geometry`.
    ##############################################################################
    def get_rgsphere(self, radius):
        """Generate a visual representation for Rhino3D

        Returns
        -------
        :class:`Rhino.Geometry.Sphere`
        """
        rg_pt = point_to_rhino(self.location_frame.point)
        return rg.Sphere(rg_pt, radius)

    def get_rgmesh(self, radius, u=8, v=4):
        """Generate mesh representation of bullet with custom resolution.

        Parameters
        ----------
        u, optional
            Number of faces in the around direction. Defaults to 8.
        v, optional
            Number of faces in the top-to-bottom direction. Defaults to 4.


        Returns
        -------
        :class:`Rhino.Geometry.Mesh`
        """
        return rg.Mesh.CreateFromSphere(self.get_rgsphere(radius), u, v)
