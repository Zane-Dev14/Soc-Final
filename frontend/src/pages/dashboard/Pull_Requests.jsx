import React from "react";
import Pull_Request_Item from "./Pull_Request_Item";

const Pull_Requests = ({ pullRequests }) => {
  return (
    <div className="h-full">
      <div className="flex flex-col gap-10">
        {pullRequests.map((pr) => (
          <Pull_Request_Item
            key={pr.pr_id}
            ghLink={pr.repo_name}
            status={pr.status}
            prLink={`https://github.com/${pr.repo_name}/pull/${pr.pr_id}`}
          />
        ))}
      </div>
    </div>
  );
};

export default Pull_Requests;
