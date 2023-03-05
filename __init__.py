import os
import re
import git
import bpy
import time

bl_info = {
    "name": "IFC git",
    "author": "Bruno Postle",
    "location": "Scene > IFC git",
    "description": "Manage IFC files in git",
    "blender": (2, 80, 0),
    "category": "Import-Export",
}

#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# 2023 Bruno Postle <bruno@postle.net>

# GUI CLASSES


class IfcGitPanel(bpy.types.Panel):
    """Scene Properties panel to interact with IFC repository data"""

    bl_label = "IFC Git"
    bl_idname = "OBJECT_PT_ifcgit"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        path_ifc = bpy.data.scenes["Scene"].BIMProperties.ifc_file
        repo = repo_from_ifc_path(path_ifc)
        if not repo:
            row = layout.row()
            row.label(text="No Git repository found", icon="SYSTEM")
            return

        row = layout.row()
        row.label(text=os.path.basename(path_ifc), icon="FILE_BLANK")

        row = layout.row()
        row.label(text=os.path.dirname(path_ifc), icon="SYSTEM")

        row = layout.row()
        row.operator("ifcgit.refresh")

        row = layout.row()
        row.template_list(
            "COMMIT_UL_List",
            "The_List",
            context.scene,
            "ifcgit_commits",
            context.scene,
            "commit_index",
        )


class ListItem(bpy.types.PropertyGroup):
    """Group of properties representing an item in the list."""

    name: bpy.props.StringProperty(
        name="Name", description="A name for this item", default="Untitled"
    )


class COMMIT_UL_List(bpy.types.UIList):
    """List of git commits"""

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):

        layout.label(text=item.name)


# OPERATORS


class RefreshGit(bpy.types.Operator):
    """Update IFC Git panel"""

    bl_label = "Refresh"
    bl_idname = "ifcgit.refresh"
    bl_options = {"REGISTER"}

    def execute(self, context):

        # ifcgit_commits is registered list widget
        context.scene.ifcgit_commits.clear()

        ifc_path = bpy.data.scenes["Scene"].BIMProperties.ifc_file
        repo = repo_from_ifc_path(ifc_path)

        commits = list(
            git.objects.commit.Commit.iter_items(
                repo=repo, rev=["HEAD"], paths=[ifc_path]
            )
        )

        for commit in commits:
            context.scene.ifcgit_commits.add()
            context.scene.ifcgit_commits[-1].name = (
                commit.author.name
                + ", "
                + time.asctime(time.gmtime(commit.committed_date))
            )

        return {"FINISHED"}


# FUNCTIONS


def repo_from_ifc_path(path_ifc):
    """Returns a Git repository object or None"""
    # FIXME doesn't work if IFC is in a sub-folder

    if not os.path.isfile(path_ifc):
        return None
    path_dir = os.path.abspath(os.path.dirname(path_ifc))
    try:
        repo = git.Repo(path_dir)
    except:
        return None
    return repo


def ifc_diff_ids(repo, hash_a, hash_b, path_ifc):
    """Given two revision hashes and a filename, retrieve"""
    """step-ids of modified, added and removed entities"""

    diff_lines = repo.git.diff(hash_a, hash_b, path_ifc).split("\n")
    inserted = set()
    deleted = set()
    for line in diff_lines:
        re_search = re.search(r"^\+#([0-9]+)=", line)
        if re_search:
            inserted.add(int(re_search.group(1)))
            continue
        re_search = re.search(r"^-#([0-9]+)=", line)
        if re_search:
            deleted.add(int(re_search.group(1)))

    return {
        "modified": inserted.intersection(deleted),
        "added": inserted.difference(modified),
        "removed": deleted.difference(modified),
    }


# uncommitted changes?
# repo.is_dirty()


def register():
    bpy.utils.register_class(IfcGitPanel)
    bpy.utils.register_class(ListItem)
    bpy.utils.register_class(COMMIT_UL_List)
    bpy.utils.register_class(RefreshGit)
    bpy.types.Scene.ifcgit_commits = bpy.props.CollectionProperty(type=ListItem)
    bpy.types.Scene.commit_index = bpy.props.IntProperty(
        name="Index for my_list", default=0
    )


def unregister():
    del bpy.types.Scene.ifcgit_commits
    del byp.types.Scene.commit_index
    bpy.utils.unregister_class(IfcGitPanel)
    bpy.utils.unregister_class(ListItem)
    bpy.utils.unregister_class(COMMIT_UL_List)
    bpy.utils.unregister_class(RefreshGit)


if __name__ == "__main__":
    register()