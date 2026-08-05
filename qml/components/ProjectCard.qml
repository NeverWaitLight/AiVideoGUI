import QtQuick 2.15

Item {
    id: card

    property int projectId: 0
    property string projectName: ""
    property string resolution: ""
    property string aspectRatio: ""
    property string coverPath: ""
    property string createdAt: ""
    property bool isGeneratingCover: false
    property int visualStyleId: 0
    property string visualStyleName: ""
    property string visualStyleImage: ""

    signal clicked()
    signal editClicked(int projectId)
    signal deleteClicked(int projectId)

    readonly property bool isVerticalVideo: aspectRatio === "9:16"

    Loader {
        anchors.fill: parent
        sourceComponent: isVerticalVideo ? portraitComponent : landscapeComponent

        Component {
            id: landscapeComponent
            ProjectCardLandscape {
                projectId: card.projectId
                projectName: card.projectName
                resolution: card.resolution
                aspectRatio: card.aspectRatio
                coverPath: card.coverPath
                createdAt: card.createdAt
                isGeneratingCover: card.isGeneratingCover
                visualStyleId: card.visualStyleId
                visualStyleName: card.visualStyleName
                visualStyleImage: card.visualStyleImage
                onClicked: card.clicked()
                onEditClicked: function(id) { card.editClicked(id) }
                onDeleteClicked: function(id) { card.deleteClicked(id) }
            }
        }

        Component {
            id: portraitComponent
            ProjectCardPortrait {
                projectId: card.projectId
                projectName: card.projectName
                resolution: card.resolution
                aspectRatio: card.aspectRatio
                coverPath: card.coverPath
                createdAt: card.createdAt
                isGeneratingCover: card.isGeneratingCover
                visualStyleId: card.visualStyleId
                visualStyleName: card.visualStyleName
                visualStyleImage: card.visualStyleImage
                onClicked: card.clicked()
                onEditClicked: function(id) { card.editClicked(id) }
                onDeleteClicked: function(id) { card.deleteClicked(id) }
            }
        }
    }
}
