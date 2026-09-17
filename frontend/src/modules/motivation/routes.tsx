import { RouteObject } from "react-router-dom";
import MotivationPage from "./components/MotivationPage";

export const motivationRoutes: RouteObject[] = [
  { path: "/motivation", element: <MotivationPage /> },
];
