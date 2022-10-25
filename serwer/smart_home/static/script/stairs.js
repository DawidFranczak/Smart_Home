async function select_stairs(){
  settings = await fetch(`/api/schody/${this.id}`);
  settings = await settings.json();
  
  document.querySelector("#lightingTime").value = settings['lightTime'];
  document.querySelector("#brightness").value = settings['brightness'];
  document.querySelector("#step").value = settings['steps'];
  document.querySelector('.stairs_containers').id = settings['sensor'];
  document.querySelector('.stairs_containers').setAttribute("style","display:block")
  if (settings["mode"]) document.querySelector('#stairs-btn').value = "Wyłącz";
  else document.querySelector('#stairs-btn').value = "Włącz";
  document.querySelector('.stairs_containers').addEventListener('click',settings_stairs);
}
  
  function settings_stairs(e){
    if(e.target.type == 'button'){
      id = document.querySelector('.stairs_containers').id;

      switch(e.target.placeholder){
        case "stairs-btn":

          dict={'action':'change-stairs',
                'id':id}
          if(this.value == "Włącz") this.value = "Wyłącz";
          else this.value = "Włącz"
          sendData('POST',dict)

          break;
        case "step":

          let step = document.querySelector('#step').value;
          if (step<1) {
            step = 1;
            document.querySelector('#step').value = 1;
          }
          if (step<1) step = 1;
          dict={'action':'set-step',
                'id':id,
                'step': step}
          sendData('POST',dict)

          break;
        case "brightness":

          let brightness = document.querySelector('#brightness').value;
          if(brightness > 100) brightness = 100;
          else if(brightness<0) brightness = 0;
          document.querySelector('#brightness').value = brightness;
          dict={'action':'set-brightness',
                'id':id,
                'brightness': brightness}
          console.log(dict)
          sendData('POST',dict)

          break;
        case "lightingTime":

          let lightTime = document.querySelector('#lightingTime').value
          if(lightTime <0 ) {
            lightTime = 0;
            document.querySelector('#lightingTime').value = 0
          }
          dict={'action':'set-lightingTime',
                'id':id,
                'lightingTime': lightTime}
          console.log(dict)
          sendData('POST',dict)

          break;
      }
    }
  }

  window.onload = function(){
    document.querySelectorAll(".button").forEach(btn => btn.addEventListener('click',select_stairs));
  }