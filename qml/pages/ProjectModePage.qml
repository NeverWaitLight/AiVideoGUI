import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: projectMode

    property string currentPage: "grid"  // grid, detail, outline, screenplay, storyboard, character, media, player, chat
    property int currentProjectId: -1

    StackLayout {
        anchors.fill: parent
        currentIndex: {
            switch (currentPage) {
                case "grid": return 0
                case "detail": return 1
                case "outline": return 2
                case "screenplay": return 3
                case "storyboard": return 4
                case "character": return 5
                case "media": return 6
                case "player": return 7
                case "chat": return 8
                default: return 0
            }
        }

        // 0: 项目网格
        ProjectGridPage {
            onProjectSelected: function(projectId) {
                projectMode.currentProjectId = projectId
                projectMode.currentPage = "detail"
            }
        }

        // 1: 项目详情（模块入口）
        ProjectDetailPage {
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "grid"
            onModuleSelected: function(moduleName) {
                projectMode.currentPage = moduleName
            }
        }

        // 2: 故事大纲
        StoryOutlinePage {
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "detail"
            onNextStepClicked: function(content) {
                bridge.screenplay.generate_script(content)
                projectMode.currentPage = "screenplay"
            }
        }

        // 3: 剧本编辑
        ScreenplayPage {
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "detail"
            onGenerateStoryboardClicked: function(pid) {
                projectMode.currentPage = "storyboard"
            }
        }

        // 4: 分镜编辑
        StoryboardPage {
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "detail"
        }

        // 5: 角色管理
        CharacterPage {
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "detail"
        }

        // 6: 素材库
        MediaLibraryPage {
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "detail"
        }

        // 7: 视频播放
        VideoPlayerPage {
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "detail"
        }

        // 8: 项目对话
        ProjectChatPage {
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "detail"
        }
    }

    function openProject(projectId) {
        currentProjectId = projectId
        currentPage = "detail"
    }
}
