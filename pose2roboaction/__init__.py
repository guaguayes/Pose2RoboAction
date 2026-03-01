import bpy
from . import properties
from . import ui
from . import operators
from .translations import translation_dict

classes = (
    properties.Pose2Robo_JointItem,
    properties.Pose2Robo_Settings,
    ui.VIEW3D_PT_Pose2Robo_Main,
    operators.Pose2Robo_OT_ExportCSV,
    operators.Pose2Robo_OT_ListAdd,
    operators.Pose2Robo_OT_ListRemoveItem,
)

def register():
    # 核心修复 1：必须在注册任何 Class 之前先加载字典！
    bpy.app.translations.register(__name__, translation_dict)
    
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.pose2robo_settings = bpy.props.PointerProperty(type=properties.Pose2Robo_Settings)

def unregister():
    del bpy.types.Scene.pose2robo_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    # 注销多语言字典
    bpy.app.translations.unregister(__name__)

if __name__ == "__main__":
    register()