# src/config/permissions.py
import nextcord


class RolePermissions:

    @staticmethod
    def get_skill_level_permissions():
        """Get permissions for all skill level roles"""
        return nextcord.PermissionOverwrite(
            # General permissions
            read_messages=True,
            send_messages=True,
            read_message_history=True,

            # Thread permissions
            create_public_threads=True,
            send_messages_in_threads=True,

            # Message permissions
            embed_links=True,
            attach_files=True,
            add_reactions=True,

            # slash command permission
            use_slash_commands = True
        )
        
    # Alias methods for each skill level role to maintain compatibility with role setup
    @staticmethod
    def get_beginner_permissions():
        """Get permissions for Beginner role"""
        return RolePermissions.get_skill_level_permissions()
        
    @staticmethod
    def get_adv_beginner_permissions():
        """Get permissions for Advanced Beginner role"""
        return RolePermissions.get_skill_level_permissions()
        
    @staticmethod
    def get_intermediate_permissions():
        """Get permissions for Intermediate role"""
        return RolePermissions.get_skill_level_permissions()
        
    @staticmethod
    def get_adv_intermediate_permissions():
        """Get permissions for Advanced Intermediate role"""
        return RolePermissions.get_skill_level_permissions()
        
    @staticmethod
    def get_advanced_permissions():
        """Get permissions for Advanced role"""
        return RolePermissions.get_skill_level_permissions()

    @staticmethod
    def get_member_permissions():
        """Get permissions for Club Member role"""
        return nextcord.PermissionOverwrite(
            # General permissions
            read_messages=True,
            send_messages=True,
            read_message_history=True,

            # Thread permissions
            create_public_threads=True,
            send_messages_in_threads=True,

            # Message permissions
            embed_links=True,
            attach_files=True,
            add_reactions=True,

            # slash command permission
            use_slash_commands = True
        )

    @staticmethod
    def get_visitor_permissions():
        """Get permissions for Court Visitor role"""
        return nextcord.PermissionOverwrite(
            read_messages=True,
            send_messages=True,
            read_message_history=True,
            add_reactions=True,
            use_slash_commands = True

        )

    @staticmethod
    def get_default_permissions():
        """Get default permissions for @everyone"""
        return nextcord.PermissionOverwrite(
            read_messages=False,
            send_messages=False
        )
