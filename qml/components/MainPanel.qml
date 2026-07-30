import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15
import "../pages" as Pages

// 主内容面板 - 中间主页面区域（项目管理/素材库）
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

    // 暴露内部页面引用，供外部访问
    readonly property alias projectModePage: projectModePage
    readonly property alias mediaLibraryPage: globalMediaPage
}
