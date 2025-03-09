"""
Add helper code to the default IGuest class.
"""

import time
import os
import virtualbox
from virtualbox import library


# Define some default params for create session
class IGuest(library.IGuest):
    __doc__ = library.IGuest.__doc__

    def create_session(
        self, user, password, domain="", session_name="pyvbox", timeout_ms=-1
    ):
        """
        # 0 in timeout_ms means immediate return NOT 'infinite' timeout like SDK suggests
        # -1 should accomplish 'infinite timeout' due to unsigned long two's complement conversion
        """
        session = super(IGuest, self).create_session(
            user, password, domain, session_name
        )
        
        waitResult = session.wait_for_array([virtualbox.library.GuestSessionWaitForFlag.start], timeout_ms)

        if waitResult != virtualbox.library.GuestSessionWaitResult.start:
            # The session is still starting because either:
            #     the waitFor timeout may have been too short
            #     the session has failed to start
            
            # We now wait for the status see what is going on. 
            error:library.VBoxError = None
            try:
                waitResult = session.wait_for_array([virtualbox.library.GuestSessionWaitForFlag.status], -1)
            except library.VBoxError as e:
                error = e
                
            if session.status != library.GuestSessionStatus.started or error is not None:
                # Something really went wrong, so close the phantom session
                session.close()
                session.wait_for_array([library.GuestSessionWaitForFlag.terminate], -1)

                if len(password) == 0:
                    raise library.VBoxError(
                        "GuestSession failed to start. Could be because of using an empty password."
                        f"VBoxError: {error}")
                else:
                    raise library.VBoxError(f"GuestSession failed to start."
                                            f"VBoxError: {error}")
        """
        # Unnecessary?
        if timeout_ms != -1:
            # There is probably a better way to to this?
            if "win" in self.os_type_id.lower():
                test_file = "C:\\Windows\\System32\\calc.exe"
            else:
                test_file = "/bin/sh"
            while True:
                try:
                    session.file_exists(test_file)
                except library.VBoxError:
                    time.sleep(0.5)
                    timeout_ms -= 500
                    if timeout_ms <= 0:
                        raise
                    continue
                break
        """
        return session

    create_session.__doc__ = library.IGuest.create_session.__doc__

    # Update guest additions helper
    def update_guest_additions(self, source=None, arguments=None, flags=None):
        if arguments is None:
            arguments = []
        if flags is None:
            flags = [library.AdditionsUpdateFlag.none]
        if source is None:
            manager = virtualbox.Manager()
            source = os.path.join(manager.bin_path, "VBoxGuestAdditions.iso")
        if not os.path.exists(source):
            raise IOError("ISO path '%s' not found" % source)

        return super(IGuest, self).update_guest_additions(source, arguments, flags)

    update_guest_additions.__doc__ = library.IGuest.update_guest_additions.__doc__
