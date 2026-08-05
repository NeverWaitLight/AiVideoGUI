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
        currentIndex: {
            if (mainPanel.currentPage === "project") return 0
            if (mainPanel.currentPage === "library") return 1
            if (mainPanel.currentPage === "visualStyles") return 2
            return 0
        }

        Pages.ProjectModePage {
            id: projectModePage
        }

        Pages.MediaLibraryPage {
            id: globalMediaPage
            onBackClicked: {
                mainPanel.currentPage = "project"
            }
        }

        Pages.VisualStyleListPage {
            id: visualStylePage
            onBackClicked: {
                mainPanel.currentPage = "project"
            }
        }
    }

    readonly property alias projectModePage: projectModePage
    readonly property alias mediaLibraryPage: globalMediaPage
    readonly property alias visualStylePage: visualStylePage
}
