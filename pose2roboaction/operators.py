import bpy
import csv
import math
import mathutils
import os
from bpy.props import IntProperty
from bpy.app.translations import pgettext_iface as iface_
from .math_utils import get_bone_axis_vector, calculate_planar_angle_0_360

class Pose2Robo_OT_ExportCSV(bpy.types.Operator):
    bl_idname = "pose2robo.export_csv"
    bl_label = "Export Data"

    _timer = None

    def invoke(self, context, event):
        scene = context.scene
        props = scene.pose2robo_settings
        obj = props.target_armature

        props.is_exporting = True
        props.export_progress = 0.0

        if not obj or obj.type != 'ARMATURE':
            props.is_exporting = False
            self.report({'ERROR'}, iface_("Please select a valid armature object in Global Settings first!"))
            return {'CANCELLED'}

        self.original_action_stored = False
        self.original_action = None
        if obj.animation_data:
            self.original_action = obj.animation_data.action
            self.original_action_stored = True
        
        if props.target_action:
            if not obj.animation_data:
                obj.animation_data_create()
            obj.animation_data.action = props.target_action

        self.valid_a_bone = None
        if props.export_root and props.root_bone:
            if props.root_bone in obj.pose.bones:
                self.valid_a_bone = props.root_bone
            else:
                props.is_exporting = False
                self.cleanup(context)
                self.report({'ERROR'}, f"{iface_('Config A Error: Bone does not exist!')} ({props.root_bone})")
                return {'CANCELLED'}

        self.valid_b_configs = []
        if props.export_joints:
            for item in props.joints_list:
                if not item.joint_name or not item.base_bone or not item.target_bone:
                    continue 
                if item.base_bone in obj.data.bones and item.target_bone in obj.data.bones:
                    self.valid_b_configs.append(item)
                else:
                    self.report({'WARNING'}, f"{iface_('Warning: Joint bone name error, skipped.')} ({item.joint_name})")

        if not self.valid_a_bone and not self.valid_b_configs:
            props.is_exporting = False
            self.cleanup(context)
            self.report({'ERROR'}, iface_("No valid export configuration, please check Config A or B!"))
            return {'CANCELLED'}

        self.rest_angles = {}
        if self.valid_b_configs:
            for item in self.valid_b_configs:
                mat_rest_x = obj.data.bones[item.base_bone].matrix_local
                mat_rest_y = obj.data.bones[item.target_bone].matrix_local
                
                vec_k = get_bone_axis_vector(mat_rest_x, item.axis_k)
                vec_i = get_bone_axis_vector(mat_rest_x, item.axis_i)
                vec_j = get_bone_axis_vector(mat_rest_y, item.axis_j)
                
                self.rest_angles[item.joint_name] = calculate_planar_angle_0_360(vec_k, vec_i, vec_j)

        self.start_f = scene.frame_start
        self.end_f = scene.frame_end

        if obj.animation_data and obj.animation_data.action:
            action = obj.animation_data.action
            self.start_f = int(action.frame_range[0])
            self.end_f = int(action.frame_range[1])
            self.report({'INFO'}, f"{iface_('Action detected, preparing to export...')} ({action.name})")
        
        self.total_frames = max(1, self.end_f - self.start_f + 1)
        self.current_f = self.start_f

        self.header = ["frame"]
        if self.valid_a_bone:
            self.header.extend([props.pos_x_name, props.pos_y_name, props.pos_z_name])
            self.header.extend([props.rot_x_name, props.rot_y_name, props.rot_z_name, props.rot_w_name])
            
        for item in self.valid_b_configs:
            self.header.append(item.joint_name)

        self.rows = []

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.001, window=context.window)
        wm.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'ESC':
            context.scene.pose2robo_settings.is_exporting = False
            self.cleanup(context)
            self.report({'WARNING'}, iface_("Export Cancelled"))
            return {'CANCELLED'}

        if event.type == 'TIMER':
            scene = context.scene
            props = scene.pose2robo_settings
            obj = props.target_armature

            batch_size = 10 
            
            try:
                for _ in range(batch_size):
                    if self.current_f > self.end_f:
                        self.finish_export(context)
                        return {'FINISHED'}

                    scene.frame_set(self.current_f)
                    context.view_layer.update() 
                    
                    row = [self.current_f]
                    
                    if self.valid_a_bone:
                        pb = obj.pose.bones[self.valid_a_bone]
                        
                        mat_world = obj.matrix_world @ pb.matrix
                        loc, rot, sca = mat_world.decompose()
                        
                        row.extend([f"{loc.x:.6f}", f"{loc.y:.6f}", f"{loc.z:.6f}"])
                        
                        corr_rad = props.correction_euler
                        if any(abs(a) > 1e-5 for a in corr_rad):
                            corr_quat = mathutils.Euler((corr_rad.x, corr_rad.y, corr_rad.z), 'XYZ').to_quaternion()
                            final_quat = rot @ corr_quat
                        else:
                            final_quat = rot
                            
                        row.extend([
                            f"{final_quat.x:.6f}", f"{final_quat.y:.6f}",
                            f"{final_quat.z:.6f}", f"{final_quat.w:.6f}"
                        ])

                    for item in self.valid_b_configs:
                        mat_curr_x = obj.pose.bones[item.base_bone].matrix
                        mat_curr_y = obj.pose.bones[item.target_bone].matrix
                        
                        vec_k = get_bone_axis_vector(mat_curr_x, item.axis_k)
                        vec_i = get_bone_axis_vector(mat_curr_x, item.axis_i)
                        vec_j = get_bone_axis_vector(mat_curr_y, item.axis_j)
                        
                        theta_curr = calculate_planar_angle_0_360(vec_k, vec_i, vec_j)
                        theta_rest = self.rest_angles[item.joint_name]
                        
                        # --- 【核心算法优化：引入 Offset 和真实 URDF 越界判定】 ---
                        
                        # 1. 计算 Blender 里的原始运动量
                        delta_blender = theta_curr - theta_rest
                        
                        # 2. 映射运动方向 (仅反转相对运动量)
                        delta_move = -delta_blender if item.is_reverse else delta_blender
                        
                        # 3. 处理用户输入的初始角度单位 (将其统一转换为度数进行计算)
                        offset_val = item.offset_angle
                        if props.angle_unit == 'RADIAN':
                            offset_deg = math.degrees(offset_val)
                        else:
                            offset_deg = offset_val
                            
                        # 4. 推算 URDF 绝对角度并归一化到圆盘
                        theta_abs = offset_deg + delta_move
                        theta_abs = theta_abs % 360.0  # 完美替代了之前的两个 while 循环
                        
                        # 5. URDF 真实阈值判定
                        if theta_abs > item.threshold:
                            final_deg = theta_abs - 360.0
                        else:
                            final_deg = theta_abs
                        
                        # 6. 单位输出
                        if props.angle_unit == 'RADIAN':
                            final_val = math.radians(final_deg)
                        else:
                            final_val = final_deg
                        # ------------------------------------------------------------
                            
                        row.append(f"{final_val:.6f}")
                        
                    self.rows.append(row)
                    self.current_f += 1

                processed = self.current_f - self.start_f
                props.export_progress = min((processed / self.total_frames) * 100.0, 100.0)

            except Exception as e:
                context.scene.pose2robo_settings.is_exporting = False
                self.cleanup(context)
                self.report({'ERROR'}, f"{iface_('Export Error')}: {e}")
                return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def finish_export(self, context):
        props = context.scene.pose2robo_settings
        props.is_exporting = False
        props.export_progress = 100.0
        
        self.cleanup(context)

        try:
            export_path = bpy.path.abspath(props.export_path)
            
            dir_name = os.path.dirname(export_path)
            if dir_name:  
                os.makedirs(dir_name, exist_ok=True)

            with open(export_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(self.header)
                writer.writerows(self.rows)
                
            def show_msg(self, context):
                self.layout.label(text=iface_("Action Mixed Export Successful!"))
                self.layout.label(text=f"{iface_('File:')} {export_path}")
                
            context.window_manager.popup_menu(show_msg, title=iface_("Export Complete"), icon='CHECKMARK')
            
        except Exception as e:
            self.report({'ERROR'}, f"[{iface_('Write Failed')}]: {e}")

    def cleanup(self, context):
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
            
        props = context.scene.pose2robo_settings
        obj = props.target_armature
        if obj and getattr(self, 'original_action_stored', False):
            if obj.animation_data:
                obj.animation_data.action = self.original_action

class Pose2Robo_OT_ListAdd(bpy.types.Operator):
    bl_idname = "pose2robo.list_add"
    bl_label = "Add"
    def execute(self, context):
        props = context.scene.pose2robo_settings
        
        props.joints_list.add()
        
        new_item_index = len(props.joints_list) - 1
        if new_item_index > 0:
            props.joints_list.move(new_item_index, 0)
            
        return {'FINISHED'}

class Pose2Robo_OT_ListRemoveItem(bpy.types.Operator):
    bl_idname = "pose2robo.list_remove_item"
    bl_label = "Remove This Item"
    index: IntProperty()
    def execute(self, context):
        props = context.scene.pose2robo_settings
        props.joints_list.remove(self.index)
        return {'FINISHED'}