import { createRootRoute, createRoute } from "@tanstack/react-router";
import { RootLayout } from "./root";
import { DashboardPage } from "./dashboard";
import { NewHuntPage } from "./new-hunt";
import { HuntDetailPage } from "./hunt-detail";
import { AutomationJobPage } from "./automation-job";
import { CRMPage } from "./crm";
import { CRMDetailPage } from "./crm-detail";
import { FollowUpsPage } from "./follow-ups";
import { SalesOpsPage } from "./sales-ops";
import { KnowledgePage } from "./knowledge";
import { DeepSeekPage } from "./deepseek";
import { SettingsPage } from "./settings";

const rootRoute = createRootRoute({ component: RootLayout });
const indexRoute = createRoute({ getParentRoute: () => rootRoute, path: "/", component: DashboardPage });
const newHuntRoute = createRoute({ getParentRoute: () => rootRoute, path: "/hunts/new", component: NewHuntPage });
const huntDetailRoute = createRoute({ getParentRoute: () => rootRoute, path: "/hunts/$huntId", component: HuntDetailPage });
const automationJobRoute = createRoute({ getParentRoute: () => rootRoute, path: "/automation/$jobId", component: AutomationJobPage });
const crmRoute = createRoute({ getParentRoute: () => rootRoute, path: "/crm", component: CRMPage });
const crmDetailRoute = createRoute({ getParentRoute: () => rootRoute, path: "/crm/$contactId", component: CRMDetailPage });
const followUpsRoute = createRoute({ getParentRoute: () => rootRoute, path: "/follow-ups", component: FollowUpsPage });
const salesOpsRoute = createRoute({ getParentRoute: () => rootRoute, path: "/sales-ops", component: SalesOpsPage });
const knowledgeRoute = createRoute({ getParentRoute: () => rootRoute, path: "/knowledge", component: KnowledgePage });
const deepSeekRoute = createRoute({ getParentRoute: () => rootRoute, path: "/deepseek", component: DeepSeekPage });
const settingsRoute = createRoute({ getParentRoute: () => rootRoute, path: "/settings", component: SettingsPage });

export const routeTree = rootRoute.addChildren([
  indexRoute, newHuntRoute, huntDetailRoute, automationJobRoute, crmRoute, crmDetailRoute,
  followUpsRoute, salesOpsRoute, knowledgeRoute, deepSeekRoute, settingsRoute,
]);
