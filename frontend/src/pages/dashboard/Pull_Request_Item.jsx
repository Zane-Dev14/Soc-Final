import React from "react";

const Pull_Request_Item = ({ id, ghLink, status, prLink }) => {
  const prStatus = status === "Merged" ? "/pr_merged.svg" : "/pr_failed.svg";
  return (
    <a
      href={prLink}
      className="bg-green-100 border-2 border-black shadow-black shadow-sm rounded-2xl flex items-center gap-5 p-5 transition-all hover:scale-[1.02]"
    >
      <img src={prStatus} alt="PR Status" className="h-8 lg:h-10 w-8 lg:w-10" />
      <h1 className="text-xl lg:text-4xl underline font-medium">{ghLink}</h1>
    </a>
  );
};

export default Pull_Request_Item;
