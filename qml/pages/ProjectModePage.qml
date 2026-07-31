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

        ProjectGridPage {
            id: projectGridPage
            onProjectSelected: function(projectId) {
                projectMode.currentProjectId = projectId
                projectMode.currentPage = "detail"
            }
        }

        ProjectDetailPage {
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "grid"
            onModuleSelected: function(moduleName) {
                projectMode.currentPage = moduleName
            }
        }

        StoryOutlinePage {
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "detail"
            onNextStepClicked: function(content) {
                bridge.screenplay.generate_script(content)
                projectMode.currentPage = "screenplay"
            }
        }

        ScreenplayPage {
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "detail"
            onGenerateStoryboardClicked: function(pid) {
                bridge.storyboard.generate_from_screenplay(pid)
                projectMode.currentPage = "storyboard"
            }
        }

        StoryboardPage {
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "detail"

            Connections {
                target: bridge.storyboard
                function onStoryboard_generated(shotCount) {
                }
                function onStoryboard_generation_failed(error) {
                }
            }
        }

        CharacterPage {
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "detail"
        }

        MediaLibraryPage {
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "detail"
        }

        VideoPlayerPage {
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "detail"
        }

        ProjectChatPage {
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "detail"
        }
    }

    function openProject(projectId) {
        currentProjectId = projectId
        currentPage = "detail"
    }

    function openCreateDialog() {
        projectGridPage.openCreateDialog()
    }
}
