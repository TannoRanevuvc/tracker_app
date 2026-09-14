import { RouteObject } from "react-router-dom";
import FinancePage from "./components/FinancePage";

export const financeRoutes: RouteObject[] = [
  { path: "/finance", element: <FinancePage /> },
];
