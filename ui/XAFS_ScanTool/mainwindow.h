#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>

#include <QMainWindow>

#include <QMessageBox>

#include <QTimer>

#include <fstream>
#include <sstream>
#include <QTextStream>
#include <QStringList>

QT_BEGIN_NAMESPACE
namespace Ui { class MainWindow; }
QT_END_NAMESPACE

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void logs();

    void on_startScan_clicked();

    void on_scanStatusVal_dbValueChanged(int out);

    void keyPressEvent(QKeyEvent *event);

    void closeEvent(QCloseEvent *event);

    void on_close_clicked();

    void on_DCMStatusInd_dbValueChanged(bool out);

private:
    Ui::MainWindow *ui;

    QString getLogText(const std::string& filePath);

    QTimer* checkLogs;

    QString mainPath = "/home/control/XAFSScanTool/";
    QString logFileName = "SED_Scantool.log";
    QString dataPath = mainPath + "DATA/";

    int scanStatus;

    bool closeFlag = 0;
};
#endif // MAINWINDOW_H
