#include "mainwindow.h"
#include "ui_mainwindow.h"

std::vector<std::string> getLastLines(std::ifstream& in, int n=10)
{
    std::vector<std::string> lines;
    std::string line;

    while(getline(in, line))
    {
        lines.push_back(line);
        if(lines.size() > static_cast<size_t>(n)) lines.erase(lines.begin());
    }
    return lines;
}

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);

    // read log file every 100 ms
    checkLogs = new QTimer(this);
    this->checkLogs->start(100);
    connect(checkLogs, SIGNAL(timeout()), this, SLOT(logs()));
}

MainWindow::~MainWindow()
{
    delete ui;
}

void MainWindow::logs()
{
    QString logText;
    logText = getLogText(mainPath.toStdString() + logFileName.toStdString());
    if(logText.isEmpty()) logText = getLogText(dataPath.toStdString() + ui->SEDPath->text().toStdString() + "/" + "*.log");
    ui->logs->setText(logText);
}

QString MainWindow::getLogText(const std::string& filePath)
{
    std::ifstream file(filePath);

    if(file)
    {
        std::vector<std::string> lastLines = getLastLines(file);
        QString logs;
        for(const std::string& line : lastLines) logs += QString::fromUtf8(line.c_str()) + "\n";
        return logs;
    }
    return QString();
}

void MainWindow::on_scanStatusVal_dbValueChanged(int out)
{
    scanStatus = out;

    switch(out)
    {
    case 0:
        ui->pause->setEnabled(false);
        ui->resume->setEnabled(false);
        ui->stop->setEnabled(false);
        ui->scanStatusInd->setColour0Property(QColor(200,200,200));
        ui->scanStatusInd->setFlashProperty(0, false);
        break;
    case 1:
        ui->pause->setEnabled(true);
        ui->resume->setEnabled(false);
        ui->stop->setEnabled(true);
        ui->scanStatusInd->setColour0Property(QColor(0,255,0));
        ui->scanStatusInd->setFlashProperty(0, false);
        break;
    case 2:
        ui->pause->setEnabled(false);
        ui->resume->setEnabled(false);
        ui->stop->setEnabled(false);
        ui->scanStatusInd->setColour0Property(QColor(0,0,255));
        ui->scanStatusInd->setFlashProperty(0, false);
        break;
    case 3:
        ui->pause->setEnabled(true);
        ui->resume->setEnabled(true);
        ui->stop->setEnabled(true);
        ui->scanStatusInd->setColour0Property(QColor(255,255,0));
        ui->scanStatusInd->setFlashProperty(0, true);
        ui->scanStatusInd->setFlashRate(QEScanTimers::Medium);
        break;
    case 4:
        ui->pause->setEnabled(false);
        ui->resume->setEnabled(false);
        ui->stop->setEnabled(true);
        ui->scanStatusInd->setColour0Property(QColor(255,0,0));
        ui->scanStatusInd->setFlashProperty(0, true);
        ui->scanStatusInd->setFlashRate(QEScanTimers::Fast);
        break;
    case 5:
        ui->stop->setEnabled(false);
        ui->pause->setEnabled(false);
        ui->resume->setEnabled(false);
        ui->scanStatusInd->setColour0Property(QColor(255,0,0));
        ui->scanStatusInd->setFlashProperty(0, true);
        ui->scanStatusInd->setFlashRate(QEScanTimers::VeryFast);
        break;
    }
}

void MainWindow::on_DCMStatusInd_dbValueChanged(bool out)
{
    ui->DCMStatusVal->setText(out ? "not move" : "moving");
}

void MainWindow::keyPressEvent(QKeyEvent *event)
{
    if(event->key() == Qt::Key_Escape) event->ignore();
}

void MainWindow::closeEvent(QCloseEvent *event)
{
    if(!closeFlag) event->ignore();
}

void MainWindow::on_close_clicked()
{
    QMessageBox::StandardButton val;
    val = QMessageBox::question(this, "Alert", "Are you sure you want to exit?", QMessageBox::Yes|QMessageBox::No);

    if(val == QMessageBox::Yes)
    {
        closeFlag = 1;
        this->close();
    }
}

