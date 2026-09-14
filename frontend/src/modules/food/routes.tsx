import { RouteObject } from "react-router-dom";
import FoodPage from "./components/FoodPage";

export const foodRoutes: RouteObject[] = [
  { path: "/food", element: <FoodPage /> },
];
