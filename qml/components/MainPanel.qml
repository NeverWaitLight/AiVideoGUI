import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15
import "../pages" as Pages

Control {
    id: mainPanel
    padding: 0

    property string currentPage: "project"

    background: Rectangle {
        color: "transparent"
    }

    contentItem: StackLayout {
        currentIndex: mainPanel.currentPage === "project" ? 0 : 1

        Pages.ProjectModePage {
            id: projectModePage
        }

        Pages.MediaLibraryPage {
            id: globalMediaPage
            onBackClicked: {
                mainPanel.currentPage = "project"
            }
        }
    }

    readonly property alias projectModePage: projectModePage
    readonly property alias mediaLibraryPage: globalMediaPage
}
