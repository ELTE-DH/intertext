const Title = ({ author, year, title }) => (
  <div>
    {`${author || 'Unknown author'}${year && ' (' + year + ')'}`}: {title}
  </div>
);
export default Title;
