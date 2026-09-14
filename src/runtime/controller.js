// HCS WorldJumper First-Person Kinematic Player Controller
// Handles pointer-lock mouse look, WASD, sprinting, crouching, jumping, gravity,
// stair-stepping, wall collision, and surface-dependent footstep triggers.

import * as THREE from 'three';

export class PlayerController {
  constructor(camera, domElement, audioManager) {
    this.camera = camera;
    this.domElement = domElement;
    this.audio = audioManager;

    this.position = new THREE.Vector3(0, 2, 10);
    this.homePosition = new THREE.Vector3(0, 2, 10);
    this.velocity = new THREE.Vector3();
    this.yaw = 0;
    this.pitch = 0;
    
    // Config
    this.walkSpeed = 5.5; // m/s
    this.sprintSpeed = 10.0;
    this.crouchSpeed = 2.8;
    this.jumpForce = 6.2;
    this.gravity = -18.0;
    this.eyeHeightStanding = 1.75;
    this.eyeHeightCrouching = 1.05;
    this.currentEyeHeight = 1.75;
    this.mouseSensitivity = 0.0022;
    this.invertY = false;

    // States
    this.isGrounded = false;
    this.isSprinting = false;
    this.isCrouching = false;
    this.isLocked = false;
    this.isIndoor = false;
    this.currentSurface = 'concrete';

    // Inputs
    this.keys = { forward: false, backward: false, left: false, right: false, jump: false, sprint: false, crouch: false };

    // Colliders reference
    this.colliders = [];
    this.downRay = new THREE.Raycaster();
    this.wallRay = new THREE.Raycaster();

    this.setupListeners();
  }

  setupListeners() {
    window.addEventListener('keydown', (e) => this.onKeyDown(e));
    window.addEventListener('keyup', (e) => this.onKeyUp(e));

    this.domElement.addEventListener('click', () => {
      if (!this.isLocked) {
        this.domElement.requestPointerLock();
      }
    });

    document.addEventListener('pointerlockchange', () => {
      this.isLocked = (document.pointerLockElement === this.domElement);
      if (this.isLocked && this.audio) {
        this.audio.resume();
      }
    });

    document.addEventListener('mousemove', (e) => {
      if (!this.isLocked) return;
      const sens = this.mouseSensitivity;
      this.yaw -= e.movementX * sens;
      const yMul = this.invertY ? -1 : 1;
      this.pitch -= e.movementY * sens * yMul;
      this.pitch = Math.max(-Math.PI * 0.48, Math.min(Math.PI * 0.48, this.pitch));
    });
  }

  onKeyDown(e) {
    if (e.code === 'KeyW' || e.code === 'ArrowUp') this.keys.forward = true;
    if (e.code === 'KeyS' || e.code === 'ArrowDown') this.keys.backward = true;
    if (e.code === 'KeyA' || e.code === 'ArrowLeft') this.keys.left = true;
    if (e.code === 'KeyD' || e.code === 'ArrowRight') this.keys.right = true;
    if (e.code === 'Space') this.keys.jump = true;
    if (e.code === 'ShiftLeft' || e.code === 'ShiftRight') this.keys.sprint = true;
    if (e.code === 'KeyC') this.keys.crouch = !this.keys.crouch; // Toggle crouch
    if (e.code === 'KeyH') {
      this.teleport(this.homePosition, false);
      console.log('HOME key pressed: Returned to safe spawn position', this.homePosition);
    }
  }

  onKeyUp(e) {
    if (e.code === 'KeyW' || e.code === 'ArrowUp') this.keys.forward = false;
    if (e.code === 'KeyS' || e.code === 'ArrowDown') this.keys.backward = false;
    if (e.code === 'KeyA' || e.code === 'ArrowLeft') this.keys.left = false;
    if (e.code === 'KeyD' || e.code === 'ArrowRight') this.keys.right = false;
    if (e.code === 'Space') this.keys.jump = false;
    if (e.code === 'ShiftLeft' || e.code === 'ShiftRight') this.keys.sprint = false;
  }

  setColliders(meshList) {
    this.colliders = meshList || [];
  }

  teleport(pos, setAsHome = true) {
    this.position.copy(pos);
    this.velocity.set(0, 0, 0);
    if (setAsHome) {
      this.homePosition.copy(pos);
    }
    // Only snap downward if within reasonable local clearance (0.5m above)
    if (this.colliders.length > 0) {
      const ray = new THREE.Raycaster(new THREE.Vector3(pos.x, pos.y + 0.5, pos.z), new THREE.Vector3(0, -1, 0), 0, 2.0);
      const hits = ray.intersectObjects(this.colliders, false);
      if (hits.length > 0) {
        this.position.y = hits[0].point.y + 0.05;
      }
    }
  }

  update(delta) {
    if (delta > 0.1) delta = 0.1; // Cap delta against hitching

    // Crouch height interpolation
    const targetHeight = this.keys.crouch ? this.eyeHeightCrouching : this.eyeHeightStanding;
    this.currentEyeHeight += (targetHeight - this.currentEyeHeight) * Math.min(1.0, delta * 12.0);

    // Direction vectors
    const forward = new THREE.Vector3(-Math.sin(this.yaw), 0, -Math.cos(this.yaw));
    const right = new THREE.Vector3(Math.cos(this.yaw), 0, -Math.sin(this.yaw));

    const moveDir = new THREE.Vector3();
    if (this.keys.forward) moveDir.add(forward);
    if (this.keys.backward) moveDir.sub(forward);
    if (this.keys.right) moveDir.add(right);
    if (this.keys.left) moveDir.sub(right);

    const isMoving = moveDir.lengthSq() > 0.001;
    if (isMoving) moveDir.normalize();

    // Speed selection
    let speed = this.walkSpeed;
    if (this.keys.crouch) speed = this.crouchSpeed;
    else if (this.keys.sprint) speed = this.sprintSpeed;

    // Horizontal acceleration & friction
    const targetVelX = moveDir.x * speed;
    const targetVelZ = moveDir.z * speed;
    const lerpRate = this.isGrounded ? 15.0 : 4.0;
    this.velocity.x += (targetVelX - this.velocity.x) * Math.min(1.0, delta * lerpRate);
    this.velocity.z += (targetVelZ - this.velocity.z) * Math.min(1.0, delta * lerpRate);

    // Gravity (only if colliders exist to prevent void falling before world loads)
    if (this.colliders.length > 0) {
      this.velocity.y += this.gravity * delta;
    } else {
      this.velocity.y = 0;
    }

    // Void floor fallback recovery
    if (this.position.y < -15.0) {
      this.position.y = 2.0;
      this.velocity.set(0, 0, 0);
    }

    // Jump
    if (this.isGrounded && this.keys.jump) {
      this.velocity.y = this.jumpForce;
      this.isGrounded = false;
      if (this.audio) this.audio.playFootstep(this.currentSurface);
    }

    // Step prediction & Horizontal wall collision
    const moveStep = new THREE.Vector3(this.velocity.x * delta, 0, this.velocity.z * delta);
    if (moveStep.lengthSq() > 0 && this.colliders.length > 0) {
      const stepDist = moveStep.length();
      const stepDir = moveStep.clone().normalize();
      
      // Raycast slightly above feet (e.g. at knee height 0.5m)
      const wallOrigin = this.position.clone().add(new THREE.Vector3(0, 0.5, 0));
      this.wallRay.set(wallOrigin, stepDir);
      this.wallRay.far = stepDist + 0.45; // Character radius ~0.4m
      
      const wallHits = this.wallRay.intersectObjects(this.colliders, false);
      if (wallHits.length > 0 && wallHits[0].distance < this.wallRay.far) {
        // Obstructed by wall: slide along normal
        const normal = wallHits[0].face.normal.clone().applyQuaternion(wallHits[0].object.quaternion);
        normal.y = 0;
        normal.normalize();
        
        // Remove normal component from velocity
        const dot = this.velocity.dot(normal);
        if (dot < 0) {
          this.velocity.sub(normal.clone().multiplyScalar(dot));
        }
      }
    }

    // Apply movement
    this.position.x += this.velocity.x * delta;
    this.position.z += this.velocity.z * delta;
    this.position.y += this.velocity.y * delta;

    // Ground raycast for terrain, floor slabs, stairs
    if (this.colliders.length > 0) {
      const rayOrigin = new THREE.Vector3(this.position.x, this.position.y + 1.2, this.position.z);
      this.downRay.set(rayOrigin, new THREE.Vector3(0, -1, 0));
      this.downRay.far = 12.0;

      const groundHits = this.downRay.intersectObjects(this.colliders, false);
      if (groundHits.length > 0) {
        const hit = groundHits[0];
        const groundY = hit.point.y;
        
        // Check if player is on or slightly below ground
        if (this.position.y <= groundY + 0.2) {
          this.position.y = groundY;
          this.velocity.y = 0;
          this.isGrounded = true;

          // Detect surface material from object name
          const name = (hit.object.name || '').toLowerCase();
          if (name.includes('floor') || name.includes('wood') || name.includes('slab')) {
            this.currentSurface = 'wood';
            this.isIndoor = true;
          } else if (name.includes('grass') || name.includes('terrain')) {
            this.currentSurface = 'grass';
            this.isIndoor = false;
          } else {
            this.currentSurface = 'concrete';
            this.isIndoor = false;
          }
        } else {
          this.isGrounded = false;
        }
      } else {
        this.isGrounded = false;
      }
    }

    // Play footstep sounds when moving on ground
    if (this.isGrounded && isMoving && this.audio) {
      this.audio.playFootstep(this.currentSurface);
    }

    // Update audio indoor/outdoor acoustic state
    if (this.audio) {
      this.audio.setIndoorState(this.isIndoor);
    }

    // Sync camera pose
    this.camera.position.set(this.position.x, this.position.y + this.currentEyeHeight, this.position.z);
    const euler = new THREE.Euler(this.pitch, this.yaw, 0, 'YXZ');
    this.camera.quaternion.setFromEuler(euler);
  }
}
