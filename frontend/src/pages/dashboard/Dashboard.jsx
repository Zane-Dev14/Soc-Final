import React, { useState, useEffect } from "react";
import Header from "../../components/Header";
import Contributed_Repos from "./Contributed_Repos";
import Pull_Requests from "./Pull_Requests";
import BASE_URL from "../../api";

const Dashboard = () => {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const response = await fetch(`${BASE_URL}/dashboard`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        });

        if (!response.ok) {
          throw new Error("Failed to fetch dashboard data");
        }

        const data = await response.json();
        setUserData(data.user);
        setLoading(false);
      } catch (error) {
        console.error("Error fetching dashboard data:", error);
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!userData) {
    return <div>Failed to load user data.</div>;
  }

  return (
    <div className="p-12 h-screen">
      <Header
        github={userData.username}
        avatar={userData.avatarurl}
      />
      <div className="w-full h-[95%] flex flex-col lg:flex-row">
        <div className="w-full h-1/2 lg:w-1/2 lg:h-[85%] overflow-hidden">
          <h1 className="text-4xl lg:text-6xl font-bold mt-10 lg:mt-20 mb-5 lg:mb-10">
            Contributed Repos
          </h1>
          <div className="w-full h-full overflow-scroll p-2 scroll-hide">
            <Contributed_Repos repos={userData.contributed_repos} />
          </div>
        </div>
        <div className="w-full h-1/2 lg:w-1/2 lg:h-[85%] overflow-hidden">
          <h1 className="text-4xl lg:text-6xl font-bold mt-10 mb-10 lg:mt-20 lg:mb-10">
            Pull Requests
          </h1>
          <div className="w-full h-full overflow-scroll p-2 scroll-hide">
            <Pull_Requests pullRequests={userData.pull_requests} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
