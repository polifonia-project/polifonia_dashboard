
const e = React.createElement;

const components = [
  {
    name:"text",
    action: Textbox
  },
  {
    name:"count",
    action: Count
  },
  {
    name:"chart",
    action: ChartViz
  },
  {
    name:"table",
    action: Table
  }
]

const RemoveComponent = ({index , removeComponent }) => {

  return (
    <>
    <a onClick={() => removeComponent(index)}
    href="#" className="trash"><i className="far fa-trash-alt"></i></a><br/>
    </>
  )
}

const SortComponent = ({index , sortComponentDown , sortComponentUp }) => {

  return (
    <>
    <a onClick={() => sortComponentDown(index)}
    href="#" className="down"><i className="fas fa-arrow-down"></i></a>
    <a onClick={() => sortComponentUp(index)}
    href="#" className="up"><i className="fas fa-arrow-up"></i></a>
    </>
  )
}

const ButtonGroup = ({ componentList , componentBoxes , buttons ,
                       addComponent , removeComponent ,
                       sortComponentUp , sortComponentDown}) => {

  if (window.location.href.indexOf("/modify/") > -1) {
    return (
      <>
        <>{componentBoxes}</>
        <section className="addfieldssection col-md-12 col-lg-12 col-sm-12">
        {buttons.map((buttonLabel, i) => (
          <a onClick={() => addComponent(buttonLabel.name,i)}
              className="btn btn-primary btn-border"
              style={{marginRight: '10px'}}
              key={i} name={buttonLabel.name}>
            Add {buttonLabel.name}
          </a>
        ))}
        </section>
      </>
    );
  } else {
    return (<>{componentBoxes}</>)
  }


};

function update_datastory(form) {
  const formData = new FormData(form);
  var url = window.location.toString()
  url = url.replace(/modify\//, 'modify_bkg\/');
  fetch(url, { method: 'POST', body: formData})
    .then(response => response.text())
    .then((data) => { datastory_data = JSON.parse(data); });
  return datastory_data;
}

function AddComponent() {

  const form = document.getElementById('modifystory_form');

  // retrieve existing components
  const stateComponents = [];
  if (datastory_data.dynamic_elements && datastory_data.dynamic_elements.length) {
    datastory_data.dynamic_elements.forEach(element => {
      const component_type = element.type ;
      let comp = components.find(o => o.name === component_type);
      stateComponents.push(comp)
    })
  }

  // save data on keyup
  if (window.location.href.indexOf("/modify/") > -1) {
    React.useEffect(() => {
      form.addEventListener('mouseout', function(event) {
        datastory_data = update_datastory(form) ;
      });
    });
  }

  const [componentList, setComponent] = React.useState(stateComponents);
  const componentBoxes = []

  // add a new component
  const addComponent = (buttonLabel,i) => {
      let comp = components.find(o => o.name === buttonLabel).action;
      setComponent(prevComponents => [
        ...prevComponents, {name:buttonLabel,action:comp}
      ])

  }

  // remove a component
  const removeComponent = (i) => {
      let newcomponentList = [...componentList];
      newcomponentList.splice(i, 1);
      setComponent(newcomponentList)
      datastory_data = update_datastory(form)
      if (datastory_data.dynamic_elements && datastory_data.dynamic_elements.length) {
        datastory_data.dynamic_elements.splice(i, 1);
        datastory_data.dynamic_elements = datastory_data.dynamic_elements.map((item, index) =>  { delete item['position']; return {"position" :index, ...item} } )
        datastory_data = update_datastory(form)
      }
  }

  // move up a component
  const sortComponentUp = (i) => {
    let newcomponentList = [...componentList];
    let cutOut = newcomponentList.splice(i, 1) [0];
    let new_i = (i === 0) ? 0: i-1; // cut the element at index 'i'
    newcomponentList.splice(new_i, 0, cutOut); // insert it at index 'new_i'
    setComponent(newcomponentList)
    datastory_data = update_datastory(form)
    console.log("UP: NOW IS",datastory_data);
    if (datastory_data.dynamic_elements.length) {
      let cutOut = datastory_data.dynamic_elements.splice(i, 1) [0];
      datastory_data.dynamic_elements.splice(new_i, 0, cutOut);
      datastory_data.dynamic_elements = datastory_data.dynamic_elements.map((item, index) =>  { delete item['position']; return {"position" :index, ...item} } )
      datastory_data = update_datastory(form)
    }
  }

  // move down a component
  const sortComponentDown = (i) => {
    let newcomponentList = [...componentList];
    let cutOut = newcomponentList.splice(i, 1) [0];
    let new_i = i+1; // cut the element at index 'from'
    newcomponentList.splice(new_i, 0, cutOut); // insert it at index 'to'
    setComponent(newcomponentList)
    datastory_data = update_datastory(form)
    console.log("DOWN: NOW IS",datastory_data);
    if (datastory_data.dynamic_elements.length) {
      let cutOut = datastory_data.dynamic_elements.splice(i, 1) [0];
      datastory_data.dynamic_elements.splice(new_i, 0, cutOut);
      datastory_data.dynamic_elements = datastory_data.dynamic_elements.map((item, index) =>  { delete item['position']; return {"position" :index, ...item} } )
      datastory_data = update_datastory(form)
    }
  }

  const generateKey = (pre) => {
      return `${ pre }_${ new Date().getTime() }`;
  }

  // push new and old components to a list and render
  for (let i = 0; i < componentList.length; i++) {
    const TargetComponent = componentList[i].action;
    componentBoxes.push(<TargetComponent
        removeComponent={removeComponent}
        sortComponentUp={sortComponentUp}
        sortComponentDown={sortComponentDown}
        index={i} key={generateKey(componentList[i].name)+i} number={i}/>)
  }

  console.log("componentList",componentList);
  console.log("componentBoxes",componentBoxes);



  return (
    <>
      <ButtonGroup
        componentList={componentList}
        addComponent={addComponent}
        removeComponent={removeComponent}
        sortComponentUp={sortComponentUp}
        sortComponentDown={sortComponentDown}
        buttons={components}
        componentBoxes={componentBoxes}></ButtonGroup>
    </>
  )
}

const domContainer = document.querySelector('#sortable');
const root = ReactDOM.createRoot(domContainer);
root.render(e(AddComponent));
