const Contributed_Repos = ({ repos }) => {
  return (
    <ul>
      {repos.map((repo, index) => (
        <li key={index} className="text-xl mb-2">
          {repo.repo_name}
        </li>
      ))}
    </ul>
  );
};

export default Contributed_Repos;
