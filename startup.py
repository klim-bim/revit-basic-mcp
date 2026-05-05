# -*- coding: utf-8 -*-

"""
Revit MCP Extension - startup file.
Registers all HTTP routes that the MCP server talks to.
Executed by pyRevit on Revit startup.
"""
import os
import sys
import imp
import traceback

try:
    from StringIO import StringIO          # IronPython / Python 2
except ImportError:
    from io import StringIO                # CPython 3

from pyrevit import routes, DB
from Autodesk.Revit.DB import (
    FilteredElementCollector, Wall, BuiltInParameter,
    Floor, RoofBase, FamilyInstance, BuiltInCategory, AttachmentLocation
)

api    = routes.API("revit_mcp")
FT2M   = 0.3048


# health check

@api.route("/ping/", methods=["GET"])
def ping(doc, request):
    return routes.make_response(data={"status": "pong", "doc": doc.Title})


# execute script

@api.route("/run_script/", methods=["POST"])
def run_script(doc, request):
    code = request.data.get("code", "")
    buf  = StringIO()
    sys.stdout, _orig = buf, sys.stdout
    try:
        exec(code, {"doc": doc, "DB": DB})
        sys.stdout = _orig
        return routes.make_response(data={"status": "success", "output": buf.getvalue()})
    except Exception as e:
        sys.stdout = _orig
        return routes.make_response(data={
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "output": buf.getvalue()
        })


# model snapshot

@api.route("/get_model_snapshot/", methods=["POST"])
def get_model_snapshot(doc, request):
    cats   = request.data.get("categories", [
        "levels", "grids", "rooms", "walls", "floors", "roofs", "columns", "windows", "doors"
    ])
    result = {"status": "success", "document": doc.Title}

    if "levels" in cats:
        result["levels"] = [
            {"id": int(l.Id.Value), "name": l.Name, "elevation_m": round(l.Elevation * FT2M, 3)}
            for l in DB.FilteredElementCollector(doc).OfClass(DB.Level).ToElements()
            if l and l.IsValidObject
        ]

    if "grids" in cats:
        result["grids"] = [
            {"id": int(g.Id.Value), "name": g.Name}
            for g in DB.FilteredElementCollector(doc).OfClass(DB.Grid).ToElements()
            if g and g.IsValidObject
        ]

    if "rooms" in cats:
        result["rooms"] = [
            {
                "id":     int(r.Id.Value),
                "name":   r.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString(),
                "number": r.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER).AsString(),
                "level":  (lambda l: l.Name if l else None)(doc.GetElement(r.LevelId))
            }
            for r in DB.FilteredElementCollector(doc)
                       .OfCategory(DB.BuiltInCategory.OST_Rooms).ToElements()
            if r and r.IsValidObject
        ]

    if "walls" in cats:
        walls = []
        for w in FilteredElementCollector(doc).OfClass(Wall).ToElements():
            if not (w and w.IsValidObject):
                continue
            curve = w.Location.Curve if w.Location else None
            loc   = None
            if curve:
                s, e = curve.GetEndPoint(0), curve.GetEndPoint(1)
                loc  = {
                    "start": {"x": round(s.X*FT2M,3), "y": round(s.Y*FT2M,3), "z": round(s.Z*FT2M,3)},
                    "end":   {"x": round(e.X*FT2M,3), "y": round(e.Y*FT2M,3), "z": round(e.Z*FT2M,3)}
                }
            level = doc.GetElement(w.LevelId)
            h     = w.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)
            o     = w.Orientation
            wt    = w.WallType
            walls.append({
                "id":               int(w.Id.Value),
                "level":            level.Name if level and level.IsValidObject else None,
                "type":             wt.LookupParameter("Type Name").AsString() if wt.LookupParameter("Type Name") else None,
                "width_m":          round(w.Width * FT2M, 3),
                "height_m":         round(h.AsDouble() * FT2M, 3) if h else None,
                "orientation":      {"x": round(o.X, 2), "y": round(o.Y, 2)},
                "attachments_top":  [int(a.Value) for a in w.GetAttachmentIds(AttachmentLocation.Top)],
                "attachments_base": [int(a.Value) for a in w.GetAttachmentIds(AttachmentLocation.Base)],
                "location":         loc
            })
        result["walls"] = walls

    if "floors" in cats:
        result["floors"] = [
            {"id": int(f.Id.Value), "level": (lambda l: l.Name if l else None)(doc.GetElement(f.LevelId))}
            for f in DB.FilteredElementCollector(doc).OfClass(DB.Floor).ToElements()
        ]

    if "roofs" in cats:
        roofs = []
        for r in DB.FilteredElementCollector(doc).OfClass(DB.RoofBase).ToElements():
            level  = doc.GetElement(r.LevelId)
            slope  = r.get_Parameter(BuiltInParameter.ROOF_SLOPE)
            fp     = []
            try:
                for loop in r.GetProfiles():
                    for mc in loop:
                        p = mc.Location.Curve.GetEndPoint(0)
                        fp.append([round(p.X*FT2M, 2), round(p.Y*FT2M, 2)])
            except:
                pass
            offset = next(
                (round(p.AsDouble()*FT2M, 3) for p in r.Parameters
                 if p.Definition.Name == "Base Offset From Level"),
                None
            )
            roofs.append({
                "id":       int(r.Id.Value),
                "level":    level.Name if level else None,
                "slope":    round(slope.AsDouble(), 4) if slope else None,
                "offset_m": offset,
                "footprint": fp
            })
        result["roofs"] = roofs

    if "columns" in cats:
        result["columns"] = [
            {
                "id":       int(c.Id.Value),
                "level":    (lambda l: l.Name if l else None)(doc.GetElement(c.LevelId)),
                "location": {"x": round(c.Location.Point.X*FT2M,3), "y": round(c.Location.Point.Y*FT2M,3)}
                            if hasattr(c.Location, "Point") else None
            }
            for c in DB.FilteredElementCollector(doc)
                       .OfCategory(DB.BuiltInCategory.OST_StructuralColumns)
                       .OfClass(DB.FamilyInstance).ToElements()
        ]

    if "windows" in cats:
        result["windows"] = [
            {"id": int(w.Id.Value), "host_id": int(w.Host.Id.Value) if w.Host else None}
            for w in DB.FilteredElementCollector(doc)
                       .OfCategory(DB.BuiltInCategory.OST_Windows)
                       .OfClass(DB.FamilyInstance).ToElements()
        ]

    if "doors" in cats:
        result["doors"] = [
            {"id": int(d.Id.Value), "host_id": int(d.Host.Id.Value) if d.Host else None}
            for d in DB.FilteredElementCollector(doc)
                       .OfCategory(DB.BuiltInCategory.OST_Doors)
                       .OfClass(DB.FamilyInstance).ToElements()
        ]

    return routes.make_response(data=result)
