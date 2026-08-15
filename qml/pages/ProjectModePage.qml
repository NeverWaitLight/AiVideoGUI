import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: projectMode

    property string currentPage: "grid"  // grid, detail, project_info, outline, screenplay, storyboard, character, media
    property int currentProjectId: -1

    StackLayout {
        anchors.fill: parent
        currentIndex: {
            switch (currentPage) {
                case "grid": return 0
                case "detail": return 1
                case "project_info": return 2
                case "outline": return 3
                case "screenplay": return 4
                case "storyboard": return 5
                case "character": return 6
                case "media": return 7
                default: return 0
            }
        }

        ProjectGridPage {
            id: projectGridPage
            onProjectSelected: function(projectId) {
                projectMode.currentProjectId = projectId
                projectMode.currentPage = "detail"
            }
            onCreateRequested: {
                var newId = bridge.projects.create_project_default("未命名项目")
                if (newId > 0) {
                    projectInfoPage.isCreate = true
                    projectMode.currentProjectId = newId
                    projectMode.currentPage = "project_info"
                }
            }
            onEditRequested: function(projectId) {
                projectInfoPage.isCreate = false
                projectMode.currentProjectId = projectId
                projectMode.currentPage = "project_info"
            }
        }

        ProjectDetailPage {
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "grid"
            onModuleSelected: function(moduleName) {
                projectMode.currentPage = moduleName
            }
        }

        ProjectInfoPage {
            id: projectInfoPage
            projectId: projectMode.currentProjectId
            onBackClicked: {
                if (isCreate) {
                    bridge.projects.delete_project(projectId)
                    projectMode.currentPage = "grid"
                } else {
                    projectMode.currentPage = "detail"
                }
            }
            onProjectSaved: function(pid) {
                projectMode.currentProjectId = pid
            }
            onNextStepClicked: {
                projectMode.currentPage = "outline"
            }
        }

        StoryOutlinePage {
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "detail"
            onNextStepClicked: function(content) {
                projectMode.currentPage = "screenplay"
            }
        }

        ScreenplayPage {
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "detail"
            onNavigateToCharacters: function(pid) {
                projectMode.currentPage = "character"
            }
        }

        StoryboardPage {
            id: storyboardPage
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "detail"
            onNavigateToMediaLibrary: function(pid) {
                projectMode.currentPage = "media"
            }
        }

        CharacterPage {
            id: characterPage
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "detail"
            onNavigateToStoryboard: function(pid) {
                projectMode.currentPage = "storyboard"
            }
        }

        MediaLibraryPage {
            id: projectMediaPage
            projectId: projectMode.currentProjectId
            onBackClicked: projectMode.currentPage = "detail"
        }
    }

    function openProject(projectId) {
        currentProjectId = projectId
        currentPage = "detail"
    }

    function openDataPage(projectId, module, entityId) {
        currentProjectId = projectId
        var target = module || "detail"
        var allowed = {
            "project_info": true,
            "outline": true,
            "screenplay": true,
            "storyboard": true,
            "character": true,
            "media": true,
            "detail": true
        }
        currentPage = allowed[target] ? target : "detail"
        if (target === "project_info") {
            projectInfoPage.isCreate = false
        }

        Qt.callLater(function() {
            if (target === "storyboard" && entityId) {
                var shotId = parseInt(entityId)
                if (!isNaN(shotId) && shotId > 0) {
                    storyboardPage.openShotDetail(shotId)
                }
            } else if (target === "character" && entityId) {
                characterPage.openCharacterDetail(entityId)
            }
        })
    }

    function openCreateDialog() {
        var newId = bridge.projects.create_project_default("未命名项目")
        if (newId > 0) {
            projectInfoPage.isCreate = true
            currentProjectId = newId
            currentPage = "project_info"
        }
    }
}
