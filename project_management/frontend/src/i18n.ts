import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Translation resources
const resources = {
  en: {
    translation: {
      // Common
      "loading": "Loading...",
      "error": "Error",
      "success": "Success",
      "save": "Save",
      "cancel": "Cancel",
      "delete": "Delete",
      "edit": "Edit",
      "close": "Close",
      "search": "Search",
      "filter": "Filter",
      "export": "Export",
      "import": "Import",

      // Project Management
      "IAICC 2025 Project Management": "IAICC 2025 Project Management",
      "International AI and Creativity Conference | Dec 13-14, 2025": "International AI and Creativity Conference | Dec 13-14, 2025",
      "IAICC 2025 Project Management Plan": "IAICC 2025 Project Management Plan",
      "Dashboard": "Dashboard",

      // Tabs
      "Gantt Chart": "Gantt Chart",
      "WBS": "WBS",
      "Deliverables": "Deliverables",
      "Milestones": "Milestones",
      "Financial": "Financial",
      "Risk Management": "Risk Management",
      "Quality": "Quality",
      "Resources": "Resources",

      // Export
      "Export CSV": "Export CSV",
      "Export to CSV": "Export to CSV",
      "Export to Excel": "Export to Excel",
      "Export to PDF": "Export to PDF",

      // Status
      "Planning": "Planning",
      "Active": "Active",
      "On Hold": "On Hold",
      "Completed": "Completed",
      "Cancelled": "Cancelled",
      "To Do": "To Do",
      "In Progress": "In Progress",
      "In Review": "In Review",
      "Blocked": "Blocked",

      // Priority
      "Low": "Low",
      "Medium": "Medium",
      "High": "High",
      "Critical": "Critical",

      // Common Labels
      "Name": "Name",
      "Description": "Description",
      "Status": "Status",
      "Priority": "Priority",
      "Start Date": "Start Date",
      "End Date": "End Date",
      "Progress": "Progress",
      "Owner": "Owner",
      "Members": "Members",
      "Tasks": "Tasks",
      "Budget": "Budget",
      "Cost": "Cost",
      "Duration": "Duration",
      "Assigned To": "Assigned To",
    }
  },
  'zh-hans': {
    translation: {
      // Common
      "loading": "加载中...",
      "error": "错误",
      "success": "成功",
      "save": "保存",
      "cancel": "取消",
      "delete": "删除",
      "edit": "编辑",
      "close": "关闭",
      "search": "搜索",
      "filter": "筛选",
      "export": "导出",
      "import": "导入",

      // Project Management
      "IAICC 2025 Project Management": "IAICC 2025 项目管理",
      "International AI and Creativity Conference | Dec 13-14, 2025": "国际人工智能与创意大会 | 2025年12月13-14日",
      "IAICC 2025 Project Management Plan": "IAICC 2025 项目管理计划",
      "Dashboard": "仪表板",

      // Tabs
      "Gantt Chart": "甘特图",
      "WBS": "工作分解结构",
      "Deliverables": "交付成果",
      "Milestones": "里程碑",
      "Financial": "财务",
      "Risk Management": "风险管理",
      "Quality": "质量",
      "Resources": "资源",

      // Export
      "Export CSV": "导出 CSV",
      "Export to CSV": "导出为 CSV",
      "Export to Excel": "导出为 Excel",
      "Export to PDF": "导出为 PDF",

      // Status
      "Planning": "计划中",
      "Active": "进行中",
      "On Hold": "暂停",
      "Completed": "已完成",
      "Cancelled": "已取消",
      "To Do": "待办",
      "In Progress": "进行中",
      "In Review": "审核中",
      "Blocked": "受阻",

      // Priority
      "Low": "低",
      "Medium": "中",
      "High": "高",
      "Critical": "紧急",

      // Common Labels
      "Name": "名称",
      "Description": "描述",
      "Status": "状态",
      "Priority": "优先级",
      "Start Date": "开始日期",
      "End Date": "结束日期",
      "Progress": "进度",
      "Owner": "负责人",
      "Members": "成员",
      "Tasks": "任务",
      "Budget": "预算",
      "Cost": "成本",
      "Duration": "持续时间",
      "Assigned To": "分配给",
    }
  }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    debug: false,
    interpolation: {
      escapeValue: false, // React already escapes values
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    }
  });

export default i18n;
